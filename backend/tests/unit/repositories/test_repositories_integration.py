from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import (
    FaceIdentity,
    FaceSample,
    IdentificationQueryFace,
    IdentificationRequest,
    Person,
    PersonPhoto,
)
from app.repositories.audit_repo import AuditRepository
from app.repositories.face_identity_repo import FaceIdentityRepository
from app.repositories.face_sample_repo import FaceSampleRepository
from app.repositories.identification_repo import IdentificationRequestRepository
from app.repositories.person_repo import PersonRepository
from app.repositories.photo_repo import PhotoRepository

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _create_person(session: AsyncSession) -> Person:
    repo = PersonRepository(session)
    return await repo.create(
        first_name="Barış",
        last_name="Özcan",
        national_id_hash="hashed_national_id_value",
        national_id_masked="******8901",
        details={"department": "Engineering"},
    )


class TestPersonRepository:
    async def test_create_persists_person(self, db_session: AsyncSession) -> None:
        repo = PersonRepository(db_session)
        person = await repo.create(
            first_name="Ali",
            last_name="Veli",
            national_id_hash="hash_ali",
            national_id_masked="******1234",
            details={"department": "HR"},
        )

        assert isinstance(person.personId, UUID)
        assert person.firstName == "Ali"
        assert person.lastName == "Veli"
        assert person.nationalIdHash == "hash_ali"
        assert person.nationalIdMasked == "******1234"
        assert person.details == {"department": "HR"}
        assert person.isActive is True

    async def test_get_by_id_returns_active_person(self, db_session: AsyncSession) -> None:
        repo = PersonRepository(db_session)
        created = await _create_person(db_session)

        fetched = await repo.get_by_id(created.personId)

        assert fetched is not None
        assert fetched.personId == created.personId

    async def test_get_by_id_returns_none_for_missing(self, db_session: AsyncSession) -> None:
        repo = PersonRepository(db_session)
        result = await repo.get_by_id(UUID("12345678-1234-7123-8123-123456789abc"))
        assert result is None

    async def test_get_by_id_skips_soft_deleted(self, db_session: AsyncSession) -> None:
        repo = PersonRepository(db_session)
        created = await _create_person(db_session)
        await repo.soft_delete(created.personId)

        fetched = await repo.get_by_id(created.personId)

        assert fetched is None

    async def test_list_active_paginates_and_counts(self, db_session: AsyncSession) -> None:
        repo = PersonRepository(db_session)
        first = await repo.create(
            first_name="First",
            last_name="Person",
            national_id_hash="hash_first",
            national_id_masked="******0001",
            details={},
        )
        second = await repo.create(
            first_name="Second",
            last_name="Person",
            national_id_hash="hash_second",
            national_id_masked="******0002",
            details={},
        )

        items, total = await repo.list_active(limit=10, offset=0)

        assert total == 2
        assert len(items) == 2
        assert {p.personId for p in items} == {first.personId, second.personId}

    async def test_update_modifies_provided_fields(self, db_session: AsyncSession) -> None:
        repo = PersonRepository(db_session)
        created = await _create_person(db_session)

        await repo.update(created, firstName="Updated")
        fetched = await repo.get_by_id(created.personId)

        assert fetched is not None
        assert fetched.firstName == "Updated"
        assert fetched.lastName == "Özcan"

    async def test_soft_delete_marks_inactive(self, db_session: AsyncSession) -> None:
        repo = PersonRepository(db_session)
        created = await _create_person(db_session)

        result = await repo.soft_delete(created.personId)
        fetched = await db_session.get(Person, created.personId)

        assert result is True
        assert fetched is not None
        assert fetched.isActive is False
        assert fetched.deletedAt is not None

    async def test_exists_by_national_id_hash(self, db_session: AsyncSession) -> None:
        repo = PersonRepository(db_session)
        created = await _create_person(db_session)

        assert await repo.exists_by_national_id_hash("hashed_national_id_value") is True
        assert await repo.exists_by_national_id_hash("missing_hash") is False

        await repo.soft_delete(created.personId)
        assert await repo.exists_by_national_id_hash("hashed_national_id_value") is False


class TestPhotoRepository:
    async def _person_and_photo(self, session: AsyncSession) -> tuple[Person, PersonPhoto]:
        person = await _create_person(session)
        repo = PhotoRepository(session)
        photo = await repo.create(
            person_id=person.personId,
            bucket="people-photos",
            key=f"{person.personId}/photo.jpg",
            content_type="image/jpeg",
            size_bytes=1024,
            width=640,
            height=480,
        )
        return person, photo

    async def test_create_persists_photo(self, db_session: AsyncSession) -> None:
        person, photo = await self._person_and_photo(db_session)

        assert isinstance(photo.photoId, UUID)
        assert photo.personId == person.personId
        assert photo.originalImageBucket == "people-photos"
        assert photo.contentType == "image/jpeg"
        assert photo.sizeBytes == 1024
        assert photo.width == 640
        assert photo.height == 480
        assert photo.isActive is True

    async def test_get_by_id_returns_active_photo(self, db_session: AsyncSession) -> None:
        _, photo = await self._person_and_photo(db_session)
        repo = PhotoRepository(db_session)

        fetched = await repo.get_by_id(photo.photoId)

        assert fetched is not None
        assert fetched.photoId == photo.photoId

    async def test_get_by_id_returns_none_for_missing(self, db_session: AsyncSession) -> None:
        repo = PhotoRepository(db_session)
        result = await repo.get_by_id(UUID("12345678-1234-7123-8123-123456789abc"))
        assert result is None

    async def test_list_active_by_person(self, db_session: AsyncSession) -> None:
        person, photo = await self._person_and_photo(db_session)
        repo = PhotoRepository(db_session)

        items, total = await repo.list_active_by_person(person.personId, limit=10, offset=0)

        assert total == 1
        assert len(items) == 1
        assert items[0].photoId == photo.photoId

    async def test_soft_delete_marks_inactive(self, db_session: AsyncSession) -> None:
        _, photo = await self._person_and_photo(db_session)
        repo = PhotoRepository(db_session)

        result = await repo.soft_delete(photo.photoId)
        fetched = await db_session.get(PersonPhoto, photo.photoId)

        assert result is True
        assert fetched is not None
        assert fetched.isActive is False
        assert fetched.deletedAt is not None


class TestFaceIdentityRepository:
    async def _person_and_identity(self, session: AsyncSession) -> tuple[Person, FaceIdentity]:
        person = await _create_person(session)
        repo = FaceIdentityRepository(session)
        identity = await repo.create_known(
            person_id=person.personId,
            display_name=f"{person.firstName} {person.lastName}",
        )
        return person, identity

    async def test_create_known_persists_identity(self, db_session: AsyncSession) -> None:
        person, identity = await self._person_and_identity(db_session)

        assert isinstance(identity.faceId, UUID)
        assert identity.identityType == "known"
        assert identity.personId == person.personId
        assert identity.displayName == "Barış Özcan"
        assert identity.isActive is True

    async def test_get_by_id_returns_active_identity(self, db_session: AsyncSession) -> None:
        _, identity = await self._person_and_identity(db_session)
        repo = FaceIdentityRepository(db_session)

        fetched = await repo.get_by_id(identity.faceId)

        assert fetched is not None
        assert fetched.faceId == identity.faceId

    async def test_list_active_by_person(self, db_session: AsyncSession) -> None:
        person, identity = await self._person_and_identity(db_session)
        repo = FaceIdentityRepository(db_session)

        items, total = await repo.list_active_by_person(person.personId, limit=10, offset=0)

        assert total == 1
        assert len(items) == 1
        assert items[0].faceId == identity.faceId

    async def test_soft_delete_marks_inactive(self, db_session: AsyncSession) -> None:
        _, identity = await self._person_and_identity(db_session)
        repo = FaceIdentityRepository(db_session)

        result = await repo.soft_delete(identity.faceId)
        fetched = await db_session.get(FaceIdentity, identity.faceId)

        assert result is True
        assert fetched is not None
        assert fetched.isActive is False


class TestFaceSampleRepository:
    async def _sample_pair(
        self, session: AsyncSession
    ) -> tuple[Person, PersonPhoto, FaceIdentity, FaceSample]:
        person = await _create_person(session)
        identity_repo = FaceIdentityRepository(session)
        identity = await identity_repo.create_known(person.personId, "Barış Özcan")
        photo_repo = PhotoRepository(session)
        photo = await photo_repo.create(
            person_id=person.personId,
            bucket="people-photos",
            key=f"{person.personId}/photo.jpg",
            content_type="image/jpeg",
            size_bytes=2048,
            width=640,
            height=480,
        )
        sample_repo = FaceSampleRepository(session)
        sample = await sample_repo.create(
            face_id=identity.faceId,
            photo_id=photo.photoId,
            qdrant_point_id=UUID("11111111-2222-7123-8123-444444444444"),
            collection_name="face_samples_arcface_w600k_r50_batch_512_batch",
            model_name="arcface_w600k_r50_batch",
            model_version="batch",
            embedding_dimension=512,
            quality_score=0.94,
            crop_bucket="face-crops",
            crop_key=f"{photo.photoId}/crop.jpg",
        )
        return person, photo, identity, sample

    async def test_create_persists_sample(self, db_session: AsyncSession) -> None:
        _, photo, identity, sample = await self._sample_pair(db_session)

        assert isinstance(sample.sampleId, UUID)
        assert sample.faceId == identity.faceId
        assert sample.photoId == photo.photoId
        assert sample.collectionName == "face_samples_arcface_w600k_r50_batch_512_batch"
        assert sample.embeddingDimension == 512
        assert sample.isIndexed is False
        assert sample.qualityScore == 0.94
        assert sample.isActive is True

    async def test_mark_indexed_sets_flag(self, db_session: AsyncSession) -> None:
        _, _, _, sample = await self._sample_pair(db_session)
        repo = FaceSampleRepository(db_session)

        result = await repo.mark_indexed(sample.sampleId)
        fetched = await db_session.get(FaceSample, sample.sampleId)

        assert result is True
        assert fetched is not None
        assert fetched.isIndexed is True

    async def test_mark_indexed_returns_false_for_missing(self, db_session: AsyncSession) -> None:
        repo = FaceSampleRepository(db_session)
        result = await repo.mark_indexed(UUID("12345678-1234-7123-8123-123456789abc"))
        assert result is False

    async def test_soft_delete_by_photo_marks_samples_inactive(
        self, db_session: AsyncSession
    ) -> None:
        _, photo, _, sample = await self._sample_pair(db_session)
        repo = FaceSampleRepository(db_session)

        deleted_count = await repo.soft_delete_by_photo(photo.photoId)
        fetched = await db_session.get(FaceSample, sample.sampleId)

        assert deleted_count == 1
        assert fetched is not None
        assert fetched.isActive is False

    async def test_list_active_by_person(self, db_session: AsyncSession) -> None:
        person, _, _, sample = await self._sample_pair(db_session)
        repo = FaceSampleRepository(db_session)

        items, total = await repo.list_active_by_person(person.personId, limit=10, offset=0)

        assert total == 1
        assert len(items) == 1
        assert items[0].sampleId == sample.sampleId

    async def test_list_active_by_person_excludes_deleted(self, db_session: AsyncSession) -> None:
        person, photo, _, sample = await self._sample_pair(db_session)
        repo = FaceSampleRepository(db_session)
        await repo.soft_delete_by_photo(photo.photoId)

        items, total = await repo.list_active_by_person(person.personId, limit=10, offset=0)

        assert total == 0
        assert len(items) == 0


class TestAuditRepository:
    async def test_log_persists_entry(self, db_session: AsyncSession) -> None:
        repo = AuditRepository(db_session)
        entity_id = UUID("12345678-1234-7123-8123-123456789abc")
        entry = await repo.log(
            action="person:create",
            entity_type="person",
            entity_id=entity_id,
            actor="api",
            request_id=None,
            outcome="success",
            safe_metadata={"source": "test"},
        )

        assert isinstance(entry.auditId, UUID)
        assert entry.action == "person:create"
        assert entry.entityType == "person"
        assert entry.entityId == entity_id
        assert entry.actor == "api"
        assert entry.outcome == "success"
        assert entry.safeMetadata == {"source": "test"}

    async def test_list_filtered_by_entity(self, db_session: AsyncSession) -> None:
        repo = AuditRepository(db_session)
        entity_id = UUID("12345678-1234-7123-8123-123456789abc")
        await repo.log(
            action="person:create",
            entity_type="person",
            entity_id=entity_id,
            actor="api",
            request_id=None,
            outcome="success",
            safe_metadata={},
        )
        await repo.log(
            action="photo:enroll",
            entity_type="person_photo",
            entity_id=UUID("abcdef12-3456-7123-8123-abcdefabcdef"),
            actor="api",
            request_id=None,
            outcome="success",
            safe_metadata={},
        )

        items, total = await repo.list_filtered(
            entity_type="person",
            entity_id=entity_id,
            action=None,
            limit=10,
            offset=0,
        )

        assert total == 1
        assert len(items) == 1
        assert items[0].action == "person:create"


class TestIdentificationRequestRepository:
    async def _request(self, session: AsyncSession) -> IdentificationRequest:
        repo = IdentificationRequestRepository(session)
        return await repo.create(top_k=5, threshold=0.55)

    async def test_create_persists_request(self, db_session: AsyncSession) -> None:
        request = await self._request(db_session)

        assert isinstance(request.requestId, UUID)
        assert request.status == "pending"
        assert request.topK == 5
        assert request.threshold == 0.55

    async def test_get_by_id_returns_request(self, db_session: AsyncSession) -> None:
        request = await self._request(db_session)
        repo = IdentificationRequestRepository(db_session)

        fetched = await repo.get_by_id(request.requestId)

        assert fetched is not None
        assert fetched.requestId == request.requestId

    async def test_list_orders_by_created_desc(self, db_session: AsyncSession) -> None:
        repo = IdentificationRequestRepository(db_session)
        await repo.create(top_k=5, threshold=None)
        await repo.create(top_k=5, threshold=None)

        items, total = await repo.list(limit=10, offset=0)

        assert total == 2
        assert items[0].createdAt >= items[1].createdAt

    async def test_add_query_faces(self, db_session: AsyncSession) -> None:
        repo = IdentificationRequestRepository(db_session)
        request = await repo.create(top_k=5, threshold=None)
        faces = [
            {
                "boundingBox": {"x": 10, "y": 20, "width": 100, "height": 100},
                "landmarks": [{"x": 1, "y": 1}],
                "qualityScore": 0.92,
            }
        ]

        created = await repo.add_query_faces(request.requestId, faces)

        assert len(created) == 1
        face = created[0]
        assert isinstance(face.queryFaceId, UUID)
        assert face.requestId == request.requestId
        assert face.boundingBox == {"x": 10, "y": 20, "width": 100, "height": 100}
        assert face.qualityScore == 0.92

    async def test_add_results(self, db_session: AsyncSession) -> None:
        repo = IdentificationRequestRepository(db_session)
        request = await repo.create(top_k=5, threshold=None)
        query_face = IdentificationQueryFace(
            requestId=request.requestId,
            boundingBox={"x": 0, "y": 0, "width": 1, "height": 1},
        )
        db_session.add(query_face)
        await db_session.flush()

        candidates = [
            {
                "faceId": None,
                "sampleId": None,
                "personId": None,
                "score": 0.75,
                "rank": 1,
                "decision": "matched",
            }
        ]
        created = await repo.add_results(request.requestId, query_face.queryFaceId, candidates)

        assert len(created) == 1
        result = created[0]
        assert isinstance(result.resultId, UUID)
        assert result.requestId == request.requestId
        assert result.queryFaceId == query_face.queryFaceId
        assert result.score == 0.75
        assert result.rank == 1
        assert result.decision == "matched"

    async def test_complete_updates_request(self, db_session: AsyncSession) -> None:
        repo = IdentificationRequestRepository(db_session)
        request = await repo.create(top_k=5, threshold=None)

        completed = await repo.complete(
            request_id=request.requestId,
            status="completed",
            decision="single_face",
            face_count=1,
            query_bucket="query-images",
            query_key=f"{request.requestId}/query.jpg",
            error_message=None,
        )

        assert completed is not None
        assert completed.status == "completed"
        assert completed.decision == "single_face"
        assert completed.faceCount == 1
        assert completed.queryImageBucket == "query-images"
        assert completed.completedAt is not None
