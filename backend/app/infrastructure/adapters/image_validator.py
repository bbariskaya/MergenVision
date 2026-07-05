"""Image format/dimension/size validation."""

from __future__ import annotations

from io import BytesIO

from PIL import Image

from app.core.config import Settings, get_settings
from app.core.errors import ValidationError
from app.infrastructure.adapters.base import ImageValidationResult


class ImageValidator:
    """Validate uploaded image bytes."""

    ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def validate(self, data: bytes) -> ImageValidationResult:
        size_bytes = len(data)
        if size_bytes > self._settings.max_upload_bytes:
            raise ValidationError(
                f"Image too large: {size_bytes} bytes (max {self._settings.max_upload_bytes})"
            )

        try:
            image = Image.open(BytesIO(data))
            image.verify()
        except Exception as exc:
            raise ValidationError(f"Invalid image: {exc}") from exc

        image = Image.open(BytesIO(data))
        content_type = (
            f"image/{image.format.lower()}" if image.format else "application/octet-stream"
        )
        if content_type not in self.ALLOWED_CONTENT_TYPES:
            raise ValidationError(f"Unsupported image format: {content_type}")

        return ImageValidationResult(
            content_type=content_type,
            width=image.width,
            height=image.height,
            size_bytes=size_bytes,
            safe_metadata={"format": image.format, "mode": image.mode},
        )
