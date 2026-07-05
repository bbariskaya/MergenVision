"""Unit tests for IdentificationService."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.application.identification_service import IdentificationService
from app.core.errors import NotFoundError
from app.domain.models import IdentificationRequest


def _make_request(
    *,
    request_id=None,
    status="completed",
    decision="single_face",
    face_count=1,
    query_bucket=None,
    query_key=None,
    query_faces=None,
    completed_at=None,
    top_k=5,
    threshold=None,
):
    request = MagicMock(spec=IdentificationRequest)
    request.requestId = request_id or uuid4()
    request.status = status
    request.decision = decision
    request.faceCount = face_count
    request.queryImageBucket = query_bucket
    request.queryImageKey = query_key
    request.query_faces = query_faces or []
    request.createdAt = datetime.now(UTC)
    request.completedAt = completed_at
    request.topK = top_k
    request.threshold = threshold
    return request


def _make_query_face(
    *,
    query_face_id=None,
    bbox=None,
    landmarks=None,
    quality_score=0.92,
    results=None,
):
    qf = MagicMock()
    qf.queryFaceId = query_face_id or uuid4()
    qf.boundingBox = bbox or {"x1": 100, "y1": 80, "x2": 220, "y2": 200}
    qf.landmarks = landmarks
    qf.qualityScore = quality_score
    qf.results = results or []
    return qf


def _make_result(**kwargs):
    r = MagicMock()
    r.rank = kwargs.get("rank", 1)
    r.faceId = kwargs.get("face_id", uuid4())
    r.personId = kwargs.get("person_id", uuid4())
    r.sampleId = kwargs.get("sample_id", uuid4())
    r.score = kwargs.get("score", 0.73)
    r.decision = kwargs.get("decision", "matched")
    return r


@pytest.fixture
def service():
    session = MagicMock()
    session.refresh = AsyncMock()
    svc = IdentificationService(
        session=session,
        face_pipeline=MagicMock(),
        storage=MagicMock(),
        vector_store=MagicMock(),
        settings=MagicMock(minio_url_expiry_seconds=3600),
    )
    svc._pipeline = MagicMock()
    svc._repo = MagicMock()
    svc._audit = MagicMock()
    return svc


@pytest.mark.asyncio
async def test_identify_forwards_selected_face_index(service):
    request = _make_request(
        query_faces=[_make_query_face(), _make_query_face()],
        decision="multiple_faces",
        face_count=2,
    )
    service._pipeline.identify = AsyncMock(return_value=request)
    service._audit.log = AsyncMock(return_value=MagicMock())
    service._object_url = AsyncMock(return_value=None)
    service._session.refresh = AsyncMock()

    response = await service.identify(
        image_bytes=b"fake",
        top_k=5,
        selected_face_index=1,
        threshold=0.55,
    )

    service._pipeline.identify.assert_awaited_once_with(
        image_bytes=b"fake",
        top_k=5,
        threshold=0.55,
        selected_face_index=1,
    )
    assert response.faceCount == 1
    assert response.decision == "single_face"
    assert len(response.faces) == 1


@pytest.mark.asyncio
async def test_identify_audits_request(service):
    request = _make_request(face_count=1, decision="single_face", top_k=5)
    service._pipeline.identify = AsyncMock(return_value=request)
    service._audit.log = AsyncMock(return_value=MagicMock())
    service._object_url = AsyncMock(return_value=None)

    await service.identify(image_bytes=b"fake")

    service._audit.log.assert_awaited_once()
    kwargs = service._audit.log.call_args.kwargs
    assert kwargs["action"] == "identification.request"
    assert kwargs["entity_type"] == "identification_request"
    assert kwargs["entity_id"] == request.requestId
    assert kwargs["request_id"] == request.requestId
    assert "faceCount" in kwargs["safe_metadata"]
    assert "topK" in kwargs["safe_metadata"]
    assert "decision" in kwargs["safe_metadata"]


@pytest.mark.asyncio
async def test_build_response_single_face(service):
    result = _make_result()
    qf = _make_query_face(results=[result])
    request = _make_request(
        query_faces=[qf],
        decision="single_face",
        face_count=1,
    )
    service._session.refresh = AsyncMock()

    response = await service._build_response(request)

    assert response.requestId == request.requestId
    assert response.faceCount == 1
    assert response.decision == "single_face"
    assert len(response.faces) == 1
    assert response.faces[0].result.rank == 1
    assert response.faces[0].boundingBox.width == 120


@pytest.mark.asyncio
async def test_build_response_multiple_faces(service):
    qf1 = _make_query_face(query_face_id=uuid4())
    qf2 = _make_query_face(query_face_id=uuid4())
    request = _make_request(
        query_faces=[qf1, qf2],
        decision="multiple_faces",
        face_count=2,
    )
    service._session.refresh = AsyncMock()

    response = await service._build_response(request)

    assert response.faceCount == 2
    assert response.decision == "multiple_faces"
    assert len(response.faces) == 2


@pytest.mark.asyncio
async def test_build_response_no_face(service):
    request = _make_request(
        query_faces=[],
        decision="no_face",
        face_count=0,
    )
    service._session.refresh = AsyncMock()

    response = await service._build_response(request)

    assert response.faceCount == 0
    assert response.decision == "no_face"
    assert response.faces == []


@pytest.mark.asyncio
async def test_build_response_presigned_query_image_url(service):
    qf = _make_query_face(results=[])
    request = _make_request(
        query_faces=[qf],
        query_bucket="query-images",
        query_key="req/image.jpg",
    )
    service._session.refresh = AsyncMock()
    service._object_url = AsyncMock(return_value="http://example.com/query.jpg")

    response = await service._build_response(request)

    assert response.queryImageUrl == "http://example.com/query.jpg"


@pytest.mark.asyncio
async def test_list_delegates_to_repo(service):
    request = _make_request()
    service._repo.list = AsyncMock(return_value=([request], 1))

    items, total = await service.list(limit=20, offset=0)

    assert total == 1
    assert items[0].requestId == request.requestId


@pytest.mark.asyncio
async def test_get_returns_response(service):
    request = _make_request(query_faces=[_make_query_face(results=[_make_result()])])
    service._repo.get_by_id = AsyncMock(return_value=request)
    service._session.refresh = AsyncMock()
    service._object_url = AsyncMock(return_value=None)

    response = await service.get(request.requestId)

    assert response.requestId == request.requestId


@pytest.mark.asyncio
async def test_get_raises_not_found(service):
    service._repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(NotFoundError):
        await service.get(uuid4())
