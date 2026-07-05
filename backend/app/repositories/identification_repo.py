"""Identification request repository."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import IdentificationQueryFace, IdentificationRequest, IdentificationResult


class IdentificationRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        top_k: int,
        threshold: float | None,
    ) -> IdentificationRequest:
        request = IdentificationRequest(topK=top_k, threshold=threshold)
        self._session.add(request)
        await self._session.flush()
        return request

    async def get_by_id(self, request_id: UUID) -> IdentificationRequest | None:
        stmt = select(IdentificationRequest).where(IdentificationRequest.requestId == request_id)
        return await self._session.scalar(stmt)

    async def list(self, limit: int, offset: int) -> tuple[list[IdentificationRequest], int]:
        stmt = (
            select(IdentificationRequest)
            .order_by(desc(IdentificationRequest.createdAt))
            .offset(offset)
            .limit(limit)
        )
        count_stmt = select(func.count()).select_from(IdentificationRequest)
        result = await self._session.execute(stmt)
        count_result = await self._session.execute(count_stmt)
        return list(result.scalars().all()), int(count_result.scalar() or 0)

    async def add_query_faces(
        self,
        request_id: UUID,
        faces: list[dict[str, Any]],
    ) -> list[IdentificationQueryFace]:
        created: list[IdentificationQueryFace] = []
        for face in faces:
            record = IdentificationQueryFace(
                requestId=request_id,
                boundingBox=face["boundingBox"],
                landmarks=face.get("landmarks"),
                qualityScore=face.get("qualityScore"),
            )
            self._session.add(record)
            created.append(record)
        await self._session.flush()
        return created

    async def add_results(
        self,
        request_id: UUID,
        query_face_id: UUID,
        candidates: list[dict[str, Any]],
    ) -> list[IdentificationResult]:
        created: list[IdentificationResult] = []
        for candidate in candidates:
            record = IdentificationResult(
                requestId=request_id,
                queryFaceId=query_face_id,
                faceId=candidate.get("faceId"),
                sampleId=candidate.get("sampleId"),
                personId=candidate.get("personId"),
                score=candidate["score"],
                rank=candidate["rank"],
                decision=candidate["decision"],
            )
            self._session.add(record)
            created.append(record)
        await self._session.flush()
        return created

    async def complete(
        self,
        request_id: UUID,
        status: str,
        decision: str | None,
        face_count: int | None,
        query_bucket: str | None,
        query_key: str | None,
        error_message: str | None,
    ) -> IdentificationRequest | None:
        request = await self.get_by_id(request_id)
        if request is None:
            return None
        request.status = status
        request.decision = decision
        request.faceCount = face_count
        request.queryImageBucket = query_bucket
        request.queryImageKey = query_key
        request.completedAt = datetime.now(UTC)
        request.errorMessage = error_message
        await self._session.flush()
        return request
