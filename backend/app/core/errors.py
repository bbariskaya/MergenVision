"""Application-wide exception hierarchy."""


class MergenVisionError(Exception):
    """Base exception for domain errors."""


class NotFoundError(MergenVisionError):
    """Requested entity does not exist."""


class ConflictError(MergenVisionError):
    """Business rule conflict (e.g. duplicate national ID)."""


class ValidationError(MergenVisionError):
    """Input failed business validation."""


class NoFaceDetectedError(ValidationError):
    """No face was detected in an image that requires exactly one face."""


class MultipleFacesDetectedError(ValidationError):
    """Multiple faces detected during enrollment, which is not allowed in Phase 1."""


class EngineNotFoundError(MergenVisionError):
    """A required TensorRT engine file is missing."""


class StorageError(MergenVisionError):
    """Object storage operation failed."""


class VectorStoreError(MergenVisionError):
    """Qdrant operation failed."""


ERROR_STATUS_MAP: dict[type[MergenVisionError], int] = {
    NotFoundError: 404,
    ConflictError: 409,
    ValidationError: 400,
    NoFaceDetectedError: 400,
    MultipleFacesDetectedError: 400,
    EngineNotFoundError: 503,
    StorageError: 502,
    VectorStoreError: 502,
}


def status_code_for_error(error: MergenVisionError) -> int:
    """Return the HTTP status code that corresponds to a domain error."""
    return ERROR_STATUS_MAP.get(type(error), 500)
