"""SQLAlchemy 2.0 ORM models for the MergenVision Phase 1 schema."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID  # noqa: N811
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.ids import new_uuid7
from app.infrastructure.db import Base


class Person(Base):
    __tablename__ = "person"

    personId: Mapped[UUID] = mapped_column(  # noqa: N815
        PgUUID(as_uuid=True),
        primary_key=True,
        default=new_uuid7,
    )
    firstName: Mapped[str | None] = mapped_column(String(255), nullable=True)  # noqa: N815
    lastName: Mapped[str | None] = mapped_column(String(255), nullable=True)  # noqa: N815
    nationalIdHash: Mapped[str | None] = mapped_column(  # noqa: N815
        String(255), nullable=True, unique=True, index=True
    )
    nationalIdMasked: Mapped[str | None] = mapped_column(String(32), nullable=True)  # noqa: N815
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    isActive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # noqa: N815
    deletedAt: Mapped[datetime | None] = mapped_column(  # noqa: N815
        DateTime(timezone=True), nullable=True
    )
    createdAt: Mapped[datetime] = mapped_column(  # noqa: N815
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updatedAt: Mapped[datetime | None] = mapped_column(  # noqa: N815
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )


class PersonPhoto(Base):
    __tablename__ = "person_photo"

    photoId: Mapped[UUID] = mapped_column(  # noqa: N815
        PgUUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    personId: Mapped[UUID] = mapped_column(  # noqa: N815
        PgUUID(as_uuid=True), ForeignKey("person.personId"), nullable=False, index=True
    )
    originalImageBucket: Mapped[str] = mapped_column(String(64), nullable=False)  # noqa: N815
    originalImageKey: Mapped[str] = mapped_column(String(512), nullable=False)  # noqa: N815
    contentType: Mapped[str] = mapped_column(String(64), nullable=False)  # noqa: N815
    sizeBytes: Mapped[int] = mapped_column(Integer, nullable=False)  # noqa: N815
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    isActive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # noqa: N815
    deletedAt: Mapped[datetime | None] = mapped_column(  # noqa: N815
        DateTime(timezone=True), nullable=True
    )
    createdAt: Mapped[datetime] = mapped_column(  # noqa: N815
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updatedAt: Mapped[datetime | None] = mapped_column(  # noqa: N815
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    person: Mapped[Person] = relationship("Person")


class FaceIdentity(Base):
    __tablename__ = "face_identity"

    faceId: Mapped[UUID] = mapped_column(  # noqa: N815
        PgUUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    # Phase 2 will add 'anonymous'; Phase 1 only 'known'.
    identityType: Mapped[str] = mapped_column(String(32), default="known", nullable=False)  # noqa: N815
    personId: Mapped[UUID | None] = mapped_column(  # noqa: N815
        PgUUID(as_uuid=True), ForeignKey("person.personId"), nullable=True, index=True
    )
    displayName: Mapped[str | None] = mapped_column(String(255), nullable=True)  # noqa: N815
    isActive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # noqa: N815
    createdAt: Mapped[datetime] = mapped_column(  # noqa: N815
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updatedAt: Mapped[datetime | None] = mapped_column(  # noqa: N815
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    person: Mapped[Person | None] = relationship("Person")


class FaceSample(Base):
    __tablename__ = "face_sample"

    sampleId: Mapped[UUID] = mapped_column(  # noqa: N815
        PgUUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    faceId: Mapped[UUID] = mapped_column(  # noqa: N815
        PgUUID(as_uuid=True), ForeignKey("face_identity.faceId"), nullable=False, index=True
    )
    photoId: Mapped[UUID | None] = mapped_column(  # noqa: N815
        PgUUID(as_uuid=True), ForeignKey("person_photo.photoId"), nullable=True, index=True
    )
    qdrantPointId: Mapped[UUID] = mapped_column(  # noqa: N815
        PgUUID(as_uuid=True), nullable=False, unique=True, index=True
    )
    collectionName: Mapped[str] = mapped_column(String(255), nullable=False, index=True)  # noqa: N815
    modelName: Mapped[str] = mapped_column(String(255), nullable=False)  # noqa: N815
    modelVersion: Mapped[str] = mapped_column(String(64), nullable=False)  # noqa: N815
    embeddingDimension: Mapped[int] = mapped_column(Integer, nullable=False)  # noqa: N815
    qualityScore: Mapped[float | None] = mapped_column(nullable=True)  # noqa: N815
    cropImageBucket: Mapped[str | None] = mapped_column(String(64), nullable=True)  # noqa: N815
    cropImageKey: Mapped[str | None] = mapped_column(String(512), nullable=True)  # noqa: N815
    isIndexed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)  # noqa: N815
    isActive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # noqa: N815
    deletedAt: Mapped[datetime | None] = mapped_column(  # noqa: N815
        DateTime(timezone=True), nullable=True
    )
    createdAt: Mapped[datetime] = mapped_column(  # noqa: N815
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updatedAt: Mapped[datetime | None] = mapped_column(  # noqa: N815
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    face: Mapped[FaceIdentity] = relationship("FaceIdentity")
    photo: Mapped[PersonPhoto | None] = relationship("PersonPhoto")


class IdentificationRequest(Base):
    __tablename__ = "identification_request"

    requestId: Mapped[UUID] = mapped_column(  # noqa: N815
        PgUUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)
    decision: Mapped[str | None] = mapped_column(String(32), nullable=True)
    faceCount: Mapped[int | None] = mapped_column(Integer, nullable=True)  # noqa: N815
    topK: Mapped[int] = mapped_column(Integer, default=5, nullable=False)  # noqa: N815
    threshold: Mapped[float | None] = mapped_column(nullable=True)
    queryImageBucket: Mapped[str | None] = mapped_column(String(64), nullable=True)  # noqa: N815
    queryImageKey: Mapped[str | None] = mapped_column(String(512), nullable=True)  # noqa: N815
    completedAt: Mapped[datetime | None] = mapped_column(  # noqa: N815
        DateTime(timezone=True), nullable=True
    )
    errorMessage: Mapped[str | None] = mapped_column(String(1024), nullable=True)  # noqa: N815
    createdAt: Mapped[datetime] = mapped_column(  # noqa: N815
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updatedAt: Mapped[datetime | None] = mapped_column(  # noqa: N815
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    query_faces: Mapped[list["IdentificationQueryFace"]] = relationship(
        "IdentificationQueryFace", back_populates="request", lazy="selectin"
    )


class IdentificationQueryFace(Base):
    __tablename__ = "identification_query_face"

    queryFaceId: Mapped[UUID] = mapped_column(  # noqa: N815
        PgUUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    requestId: Mapped[UUID] = mapped_column(  # noqa: N815
        PgUUID(as_uuid=True),
        ForeignKey("identification_request.requestId"),
        nullable=False,
        index=True,
    )
    boundingBox: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)  # noqa: N815
    landmarks: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    qualityScore: Mapped[float | None] = mapped_column(nullable=True)  # noqa: N815
    createdAt: Mapped[datetime] = mapped_column(  # noqa: N815
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updatedAt: Mapped[datetime | None] = mapped_column(  # noqa: N815
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    request: Mapped[IdentificationRequest] = relationship(
        "IdentificationRequest", back_populates="query_faces"
    )
    results: Mapped[list["IdentificationResult"]] = relationship(
        "IdentificationResult", back_populates="query_face", lazy="selectin"
    )


class IdentificationResult(Base):
    __tablename__ = "identification_result"

    resultId: Mapped[UUID] = mapped_column(  # noqa: N815
        PgUUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    requestId: Mapped[UUID] = mapped_column(  # noqa: N815
        PgUUID(as_uuid=True),
        ForeignKey("identification_request.requestId"),
        nullable=False,
        index=True,
    )
    queryFaceId: Mapped[UUID] = mapped_column(  # noqa: N815
        PgUUID(as_uuid=True),
        ForeignKey("identification_query_face.queryFaceId"),
        nullable=False,
        index=True,
    )
    faceId: Mapped[UUID | None] = mapped_column(  # noqa: N815
        PgUUID(as_uuid=True), ForeignKey("face_identity.faceId"), nullable=True, index=True
    )
    sampleId: Mapped[UUID | None] = mapped_column(  # noqa: N815
        PgUUID(as_uuid=True), ForeignKey("face_sample.sampleId"), nullable=True
    )
    personId: Mapped[UUID | None] = mapped_column(  # noqa: N815
        PgUUID(as_uuid=True), ForeignKey("person.personId"), nullable=True
    )
    score: Mapped[float] = mapped_column(nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    createdAt: Mapped[datetime] = mapped_column(  # noqa: N815
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updatedAt: Mapped[datetime | None] = mapped_column(  # noqa: N815
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    request: Mapped[IdentificationRequest] = relationship("IdentificationRequest")
    query_face: Mapped[IdentificationQueryFace] = relationship(
        "IdentificationQueryFace", back_populates="results"
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    auditId: Mapped[UUID] = mapped_column(  # noqa: N815
        PgUUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    entityType: Mapped[str | None] = mapped_column(String(128), nullable=True)  # noqa: N815
    entityId: Mapped[UUID | None] = mapped_column(  # noqa: N815
        PgUUID(as_uuid=True), nullable=True, index=True
    )
    actor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    requestId: Mapped[UUID | None] = mapped_column(  # noqa: N815
        PgUUID(as_uuid=True), nullable=True, index=True
    )
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    safeMetadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)  # noqa: N815
    createdAt: Mapped[datetime] = mapped_column(  # noqa: N815
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updatedAt: Mapped[datetime | None] = mapped_column(  # noqa: N815
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
