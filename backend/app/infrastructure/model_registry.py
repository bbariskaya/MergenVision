"""Model registry resolves model file paths and metadata from settings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings, get_settings
from app.core.errors import EngineNotFoundError


@dataclass(frozen=True)
class ModelInfo:
    name: str
    version: str
    local_path: Path
    input_size: int | None
    output_dim: int | None


class ModelRegistry:
    """Resolves detector and recognizer model metadata."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._models_dir = self._settings.models_dir

    def get_detector(self) -> ModelInfo:
        path = self._models_dir / self._settings.detector_model_name
        name = Path(self._settings.detector_model_name).stem
        return ModelInfo(
            name=name,
            version="batch",
            local_path=path,
            input_size=self._settings.detector_input_size,
            output_dim=None,
        )

    def get_recognizer(self) -> ModelInfo:
        path = self._models_dir / self._settings.recognizer_model_name
        name = Path(self._settings.recognizer_model_name).stem
        return ModelInfo(
            name=name,
            version="batch",
            local_path=path,
            input_size=None,
            output_dim=512,
        )

    def trt_engine_path(
        self,
        model_info: ModelInfo,
        batch_size: int,
    ) -> Path:
        """Return the expected TensorRT engine path for a static batch size."""
        file_name = f"{model_info.name}.onnx_batch_{batch_size}.plan"
        path = self._settings.trt_engine_dir / file_name
        if not path.exists():
            raise EngineNotFoundError(
                f"TensorRT engine not found: {path}. "
                "Run scripts/build_trt_engines.py on a matching GPU environment."
            )
        return path


def get_model_registry(settings: Settings | None = None) -> ModelRegistry:
    return ModelRegistry(settings)
