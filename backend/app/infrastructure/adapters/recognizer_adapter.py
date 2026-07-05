"""ArcFace recognizer adapter using TensorRT and torch."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from app.core.config import Settings, get_settings
from app.core.errors import EngineNotFoundError
from app.infrastructure.adapters.base import EmbeddingBatch
from app.infrastructure.adapters.trt_session import TrtInferenceSession
from app.infrastructure.model_registry import ModelRegistry, get_model_registry

if TYPE_CHECKING:
    import torch

logger = logging.getLogger(__name__)


class RecognizerAdapter:
    """ArcFace-style recognizer using a batched TensorRT engine.

    Expects aligned RGB face crops as a ``[M, 3, 112, 112]`` torch tensor with
    pixel values in ``[0, 255]``. Pre-processing mirrors InsightFace's
    ``ArcFaceONNX.get_feat``: subtract ``input_mean`` and divide by ``input_std``
    (no BGR swap because the input is already RGB). Outputs are L2-normalized.
    """

    def __init__(
        self,
        registry: ModelRegistry | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._registry = registry or get_model_registry(self._settings)
        self._model_info = self._registry.get_recognizer()
        self._sessions: dict[int, TrtInferenceSession] = {}
        self._mean = self._settings.recognizer_mean
        self._std = self._settings.recognizer_std

    @property
    def name(self) -> str:
        return self._model_info.name

    @property
    def version(self) -> str:
        return self._settings.recognizer_version

    @property
    def embedding_dimension(self) -> int:
        return self._settings.recognizer_embedding_dimension

    @property
    def input_size(self) -> int:
        return self._settings.recognizer_input_size

    def _select_batch_size(self, n: int) -> int:
        for size in self._settings.trt_batch_profiles:
            if size >= n:
                return size
        return max(self._settings.trt_batch_profiles)

    def _get_session(self, batch_size: int) -> TrtInferenceSession:
        if batch_size not in self._sessions:
            try:
                path = self._registry.trt_engine_path(self._model_info, batch_size)
            except EngineNotFoundError:
                available = sorted(
                    int(p.stem.split("_batch_")[-1])
                    for p in self._settings.trt_engine_dir.glob("*.plan")
                    if self._model_info.name in p.name
                )
                if not available:
                    raise
                fallback = min(s for s in available if s >= batch_size)
                path = self._registry.trt_engine_path(self._model_info, fallback)
            self._sessions[batch_size] = TrtInferenceSession(path)
        return self._sessions[batch_size]

    def embed(
        self,
        faces: torch.Tensor | list[NDArray[np.uint8]],
    ) -> EmbeddingBatch:
        """Return L2-normalized embeddings for a batch of aligned RGB crops."""
        import torch

        if len(faces) == 0:
            return EmbeddingBatch(
                embeddings=np.zeros((0, self.embedding_dimension), dtype=np.float32),
                model_name=self.name,
                model_version=self.version,
                dimension=self.embedding_dimension,
            )

        tensor = self._to_tensor(faces)
        if (
            tensor.shape[1] != 3
            or tensor.shape[2] != self.input_size
            or tensor.shape[3] != self.input_size
        ):
            raise ValueError(
                f"Recognizer expects [M,3,{self.input_size},{self.input_size}], "
                f"got {tuple(tensor.shape)}"
            )

        n = tensor.shape[0]
        max_profile = max(self._settings.trt_batch_profiles)
        chunks = [tensor[i : i + max_profile] for i in range(0, n, max_profile)]

        all_embeddings: list[np.ndarray] = []
        for chunk in chunks:
            chunk_size = chunk.shape[0]
            batch_size = self._select_batch_size(chunk_size)
            session = self._get_session(batch_size)

            if chunk_size < batch_size:
                padding = torch.zeros(
                    (batch_size - chunk_size, 3, self.input_size, self.input_size),
                    dtype=chunk.dtype,
                    device=chunk.device,
                )
                padded = torch.cat([chunk, padding], dim=0)
            else:
                padded = chunk

            normalized = (padded - self._mean) / self._std
            outputs = session.infer(normalized)
            all_embeddings.append(outputs[0][:chunk_size])

        embeddings = (
            np.concatenate(all_embeddings, axis=0)
            if all_embeddings
            else np.zeros((0, self.embedding_dimension), dtype=np.float32)
        )

        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized_emb = np.divide(
            embeddings,
            norms,
            out=np.zeros_like(embeddings),
            where=norms != 0,
        )
        return EmbeddingBatch(
            embeddings=normalized_emb,
            model_name=self.name,
            model_version=self.version,
            dimension=self.embedding_dimension,
        )

    def _to_tensor(
        self,
        faces: torch.Tensor | list[NDArray[np.uint8]],
    ) -> torch.Tensor:
        import torch

        if isinstance(faces, torch.Tensor):
            return faces

        images: list[torch.Tensor] = []
        for arr in faces:
            if arr.shape != (self.input_size, self.input_size, 3):
                raise ValueError(f"Each face must be (H,W,3), got {tuple(arr.shape)}")
            # Input is BGR numpy (legacy); convert to RGB.
            rgb = arr[..., ::-1]
            t = torch.from_numpy(rgb.astype(np.float32)).permute(2, 0, 1)
            images.append(t)
        return torch.stack(images)
