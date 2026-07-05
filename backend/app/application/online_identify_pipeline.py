"""Online identification orchestration."""

from __future__ import annotations

import asyncio
from uuid import UUID

from app.core.config import Settings, get_settings
from app.core.errors import ValidationError
from app.core.ids import new_uuid7
from app.domain.models import IdentificationRequest
from app.infrastructure.adapters.base import QueryFaceOutput
from app.infrastructure.adapters.pipelines import FacePipeline
from app.infrastructure.storage import ObjectStorage
from app.infrastructure.vector_store import SearchHit, VectorStore
from app.repositories.identification_repo import IdentificationRequestRepository


class OnlineIdentifyPipeline:
    """Identify faces in a query image against the enrolled collection."""

    _DECISION_MATCHED = "matched"
    _DECISION_POSSIBLE = "possible_match"
    _DECISION_NO_MATCH = "no_match"

    def __init__(
        self,
        face_pipeline: FacePipeline | None = None,
        request_repo: IdentificationRequestRepository | None = None,
        storage: ObjectStorage | None = None,
        vector_store: VectorStore | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._face_pipeline = face_pipeline
        self._request_repo = request_repo
        self._storage = storage
        self._vector_store = vector_store

    async def identify(
        self,
        image_bytes: bytes,
        top_k: int | None = None,
        threshold: float | None = None,
        selected_face_index: int | None = None,
    ) -> IdentificationRequest:
        """Run identification and persist the request with results."""
        if self._face_pipeline is None or self._request_repo is None:
            raise RuntimeError("OnlineIdentifyPipeline is not fully wired")

        top_k = min(top_k or self._settings.default_top_k, self._settings.max_top_k)
        matched_threshold = threshold or self._settings.matched_threshold
        possible_threshold = self._settings.possible_match_threshold

        request = await self._request_repo.create(top_k=top_k, threshold=matched_threshold)

        query_bucket: str | None = None
        query_key: str | None = None
        if self._settings.store_query_images:
            query_key = f"{request.requestId}/{new_uuid7()}.jpg"
            await self._storage.upload(
                bucket=self._settings.minio_bucket_query_images,
                key=query_key,
                data=image_bytes,
                content_type="image/jpeg",
            )
            query_bucket = self._settings.minio_bucket_query_images

        try:
            detected_faces = await self._run_face_pipeline(image_bytes)
            if selected_face_index is not None:
                if selected_face_index < 0 or selected_face_index >= len(detected_faces):
                    raise ValidationError("selected_face_index is out of range")
                query_faces = [detected_faces[selected_face_index]]
            else:
                query_faces = detected_faces

            query_face_records = await self._request_repo.add_query_faces(
                request_id=request.requestId,
                faces=[self._query_face_record(face) for face in query_faces],
            )

            for face, query_face_record in zip(query_faces, query_face_records, strict=True):
                hits = await self._search(face)
                candidates = self._rank_and_decide(
                    hits,
                    top_k=top_k,
                    matched_threshold=matched_threshold,
                    possible_threshold=possible_threshold,
                )
                await self._request_repo.add_results(
                    request_id=request.requestId,
                    query_face_id=query_face_record.queryFaceId,
                    candidates=candidates,
                )

            decision = self._aggregate_decision(detected_faces)
            await self._request_repo.complete(
                request_id=request.requestId,
                status="completed",
                decision=decision,
                face_count=len(detected_faces),
                query_bucket=query_bucket,
                query_key=query_key,
                error_message=None,
            )
        except Exception as exc:
            await self._request_repo.complete(
                request_id=request.requestId,
                status="failed",
                decision=None,
                face_count=None,
                query_bucket=query_bucket,
                query_key=query_key,
                error_message=str(exc),
            )
            raise

        return request

    async def _run_face_pipeline(self, image_bytes: bytes) -> list[QueryFaceOutput]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._face_pipeline.identify_prepare, image_bytes)

    @staticmethod
    def _query_face_record(face: QueryFaceOutput) -> dict:
        return {
            "boundingBox": {
                "x1": face.bbox[0],
                "y1": face.bbox[1],
                "x2": face.bbox[2],
                "y2": face.bbox[3],
            },
            "landmarks": [{"x": x, "y": y} for x, y in (face.landmarks or [])],
            "qualityScore": face.quality_score,
        }

    async def _search(self, face: QueryFaceOutput) -> list[SearchHit]:
        if self._vector_store is None:
            raise RuntimeError("VectorStore is not wired")
        return await self._vector_store.search(
            model_name=self._face_pipeline.recognizer_name,
            dimension=face.embedding.shape[0] if hasattr(face.embedding, "shape") else 512,
            version=self._face_pipeline.recognizer_version,
            embedding=face.embedding,
            top_k=self._settings.max_top_k,
            active_only=True,
        )

    def _rank_and_decide(
        self,
        hits: list[SearchHit],
        top_k: int,
        matched_threshold: float,
        possible_threshold: float,
    ) -> list[dict]:
        candidates: list[dict] = []
        for rank, hit in enumerate(hits[:top_k], start=1):
            if hit.score >= matched_threshold:
                decision = self._DECISION_MATCHED
            elif hit.score >= possible_threshold:
                decision = self._DECISION_POSSIBLE
            else:
                decision = self._DECISION_NO_MATCH
            candidates.append(
                {
                    "faceId": UUID(hit.payload["faceId"]) if "faceId" in hit.payload else None,
                    "sampleId": UUID(hit.payload["sampleId"])
                    if "sampleId" in hit.payload
                    else None,
                    "personId": UUID(hit.payload["personId"])
                    if "personId" in hit.payload
                    else None,
                    "score": hit.score,
                    "rank": rank,
                    "decision": decision,
                }
            )
        return candidates

    @staticmethod
    def _aggregate_decision(faces: list[QueryFaceOutput]) -> str:
        count = len(faces)
        if count == 0:
            return "no_face"
        if count == 1:
            return "single_face"
        return "multiple_faces"
