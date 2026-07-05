"""Base types and data classes for the ML adapter boundary."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class Detection:
    """A single face detection in a batch."""

    image_index: int
    bbox: tuple[float, float, float, float]
    score: float
    landmarks: list[tuple[float, float]]


@dataclass(frozen=True)
class DetectionBatch:
    """Batch of detections across one or more images."""

    detections: tuple[Detection, ...] = ()
    image_count: int = 0

    def __iter__(self) -> Iterator[Detection]:
        return iter(self.detections)

    def __len__(self) -> int:
        return len(self.detections)

    @property
    def by_image(self) -> dict[int, list[Detection]]:
        groups: dict[int, list[Detection]] = {index: [] for index in range(self.image_count)}
        for detection in self.detections:
            groups[detection.image_index].append(detection)
        return groups


@dataclass(frozen=True)
class EmbeddingBatch:
    """Batch of face embeddings."""

    embeddings: NDArray[np.float32]
    model_name: str
    model_version: str
    dimension: int


@dataclass(frozen=True)
class EnrollOutput:
    """Output of `FacePipeline.enroll`."""

    crop_bytes: bytes
    embedding: NDArray[np.float32]
    bbox: tuple[float, float, float, float]
    landmarks: list[tuple[float, float]]
    quality_score: float
    model_name: str
    model_version: str
    dimension: int


@dataclass(frozen=True)
class LazyEnrollOutput:
    """GPU/CPU raw output before JPEG encoding."""

    crop_tensor: NDArray[np.uint8]  # CHW RGB uint8
    embedding: NDArray[np.float32]
    bbox: tuple[float, float, float, float]
    landmarks: list[tuple[float, float]]
    quality_score: float
    model_name: str
    model_version: str
    dimension: int


@dataclass(frozen=True)
class QueryFaceOutput:
    """Output of `FacePipeline.identify_prepare` for one detected face."""

    embedding: NDArray[np.float32]
    bbox: tuple[float, float, float, float]
    landmarks: list[tuple[float, float]] | None
    quality_score: float | None


@dataclass(frozen=True)
class ImageValidationResult:
    """Result of validating an uploaded image."""

    content_type: str
    width: int
    height: int
    size_bytes: int
    safe_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EnrollBatchResult:
    """Result of `BatchEnrollmentPipeline.enroll_batch`."""

    person_id: UUID
    photo_count: int
    face_count: int
    sample_count: int
    photo_ids: list[UUID]
    face_ids: list[UUID]
    sample_ids: list[UUID]
