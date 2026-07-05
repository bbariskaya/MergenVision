"""Identification application service."""

from __future__ import annotations

import asyncio
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.online_identify_pipeline import OnlineIdentifyPipeline
from app.core.config import Settings, get_settings
from app.core.errors import NotFoundError, ValidationError
from app.domain.models import IdentificationRequest
from app.infrastructure.adapters.pipelines import FacePipeline
from app.infrastructure.storage import ObjectStorage, get_object_storage
from app.infrastructure.vector_store import VectorStore, get_vector_store
from app.repositories.audit_repo import AuditRepository
from app.repositories.face_sample_repo import FaceSampleRepository
from app.repositories.identification_repo import IdentificationRequestRepository
from app.schemas.identify import (
    BoundingBox,
    Candidate,
    IdentificationRequestSummary,
    IdentifyFaceResult,
    IdentifyResponse,
)


class IdentificationService:
    """Service wrapper around ``OnlineIdentifyPipeline``."""

    def __init__(
        self,
        session: AsyncSession,
        face_pipeline: FacePipeline | None = None,
        storage: ObjectStorage | None = None,
        vector_store: VectorStore | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._repo = IdentificationRequestRepository(session)
        self._sample_repo = FaceSampleRepository(session)
        self._pipeline = OnlineIdentifyPipeline(
            face_pipeline=face_pipeline or FacePipeline(settings=self._settings),
            request_repo=self._repo,
            storage=storage or get_object_storage(settings=self._settings),
            vector_store=vector_store or get_vector_store(settings=self._settings),
            settings=self._settings,
        )
        self._audit = AuditRepository(session)

    async def identify(
        self,
        image_bytes: bytes,
        top_k: int | None = None,
        threshold: float | None = None,
        selected_face_index: int | None = None,
    ) -> IdentifyResponse:
        request = await self._pipeline.identify(
            image_bytes=image_bytes,
            top_k=top_k,
            threshold=threshold,
            selected_face_index=selected_face_index,
        )
        await self._audit.log(
            action="identification.request",
            entity_type="identification_request",
            entity_id=request.requestId,
            actor=None,
            request_id=request.requestId,
            outcome=request.status,
            safe_metadata={
                "faceCount": request.faceCount,
                "topK": request.topK,
                "decision": request.decision,
            },
        )
        return await self._build_response(request, selected_face_index=selected_face_index)

    async def get(self, request_id: UUID) -> IdentifyResponse:
        request = await self._load(request_id)
        return await self._build_response(request)

    async def list(
        self,
        limit: int,
        offset: int,
    ) -> tuple[list[IdentificationRequestSummary], int]:
        requests, total = await self._repo.list(limit=limit, offset=offset)
        return [IdentificationRequestSummary.model_validate(r) for r in requests], total

    async def _load(self, request_id: UUID) -> IdentificationRequest:
        request = await self._repo.get_by_id(request_id)
        if request is None:
            raise NotFoundError("Identification request not found")
        return request

    async def _build_response(
        self,
        request: IdentificationRequest,
        selected_face_index: int | None = None,
    ) -> IdentifyResponse:
        query_image_url: str | None = None
        if request.queryImageBucket and request.queryImageKey:
            query_image_url = await self._object_url(
                request.queryImageBucket,
                request.queryImageKey,
            )

        # Eager-load children to avoid extra round-trips.
        await self._session.refresh(
            request,
            attribute_names=["query_faces"],
        )
        for qf in request.query_faces:
            await self._session.refresh(
                qf,
                attribute_names=["results"],
            )

        query_faces = list(request.query_faces)
        decision = request.decision
        face_count = request.faceCount
        if selected_face_index is not None:
            if selected_face_index < 0 or selected_face_index >= len(query_faces):
                raise ValidationError("selected_face_index is out of range")
            query_faces = [query_faces[selected_face_index]]
            decision = "single_face"
            face_count = 1

        # Resolve crop image URLs for all candidate samples.
        sample_ids: set[UUID] = {
            r.sampleId
            for qf in query_faces
            for r in qf.results
            if r.sampleId is not None
        }
        crop_info = await self._sample_repo.get_crop_info_by_sample_ids(
            list(sample_ids),
        )
        crop_url_tasks = []
        crop_sample_ids: list[UUID] = []
        for sample_id, (bucket, key) in crop_info.items():
            if bucket and key:
                crop_url_tasks.append(self._object_url(bucket, key))
                crop_sample_ids.append(sample_id)
        crop_urls_list = await asyncio.gather(*crop_url_tasks, return_exceptions=True)
        crop_urls: dict[UUID, str] = {}
        for sample_id, url in zip(crop_sample_ids, crop_urls_list, strict=False):
            if isinstance(url, str):
                crop_urls[sample_id] = url

        faces: list[IdentifyFaceResult] = []
        for qf in query_faces:
            bbox_dict = qf.boundingBox or {}
            bbox = BoundingBox(
                x=int(bbox_dict.get("x1", 0)),
                y=int(bbox_dict.get("y1", 0)),
                width=int(bbox_dict.get("x2", 0)) - int(bbox_dict.get("x1", 0)),
                height=int(bbox_dict.get("y2", 0)) - int(bbox_dict.get("y1", 0)),
            )
            candidates = [
                Candidate(
                    rank=r.rank,
                    faceId=r.faceId,
                    personId=r.personId,
                    sampleId=r.sampleId,
                    name=None,  # names are resolved in the router layer to keep this simple.
                    score=r.score,
                    decision=r.decision,
                    cropImageUrl=crop_urls.get(r.sampleId),
                )
                for r in sorted(qf.results, key=lambda x: x.rank)
            ]
            top = candidates[0] if candidates else None
            faces.append(
                IdentifyFaceResult(
                    queryFaceId=qf.queryFaceId,
                    boundingBox=bbox,
                    qualityScore=qf.qualityScore,
                    result=top,
                    candidates=candidates,
                )
            )

        return IdentifyResponse(
            requestId=request.requestId,
            status=request.status,
            decision=decision,
            faceCount=face_count,
            queryImageUrl=query_image_url,
            faces=faces,
            createdAt=request.createdAt,
            completedAt=request.completedAt,
        )

    async def _object_url(self, bucket: str, key: str) -> str:
        storage = get_object_storage(settings=self._settings)
        return await storage.presigned_get_url(
            bucket=bucket,
            key=key,
            expires=self._settings.minio_url_expiry_seconds,
        )
