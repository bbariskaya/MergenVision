"""High-level face ML pipelines."""

from __future__ import annotations

import concurrent.futures
from collections.abc import Iterator
from dataclasses import dataclass
from io import BytesIO
from typing import TYPE_CHECKING

import numpy as np
from PIL import Image

from app.core.config import Settings, get_settings
from app.infrastructure.adapters.aligner_preprocessor import AlignerPreprocessor
from app.infrastructure.adapters.base import (
    DetectionBatch,
    EmbeddingBatch,
    EnrollOutput,
    ImageValidationResult,
    LazyEnrollOutput,
    QueryFaceOutput,
)
from app.infrastructure.adapters.detector_adapter import DetectorAdapter
from app.infrastructure.adapters.gpu_dali_decoder import GpuDaliDecoder
from app.infrastructure.adapters.gpu_pil_decoder import GpuPilDecoder
from app.infrastructure.adapters.image_validator import ImageValidator
from app.infrastructure.adapters.recognizer_adapter import RecognizerAdapter
from app.infrastructure.adapters.torch_preprocessor import TorchPreprocessor

if TYPE_CHECKING:
    import torch


@dataclass(frozen=True)
class PreparedImage:
    """Decoded image with its original and model-input tensors."""

    original_tensor: torch.Tensor  # [3, H, W] RGB, 0..255
    model_input: torch.Tensor  # [3, input_size, input_size] RGB normalized
    original_size: tuple[int, int]
    content_type: str


class FacePipeline:
    """End-to-end detect/align/recognize orchestration.

    Follows the InsightFace ``FaceAnalysis`` pattern: detect with SCRFD,
    align each face with the ArcFace 5-point template, then recognize with
    ArcFace. All heavy ops run on the configured GPU when available.
    """

    def __init__(
        self,
        detector: DetectorAdapter | None = None,
        aligner: AlignerPreprocessor | None = None,
        recognizer: RecognizerAdapter | None = None,
        validator: ImageValidator | None = None,
        decoder: GpuPilDecoder | None = None,
        preprocessor: TorchPreprocessor | None = None,
        dali_decoder: GpuDaliDecoder | None = None,
        decoder_backend: str = "auto",
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._detector = detector or DetectorAdapter(settings=self._settings)
        self._aligner = aligner or AlignerPreprocessor(device_id=self._settings.gpu_device_id)
        self._recognizer = recognizer or RecognizerAdapter(settings=self._settings)
        self._validator = validator or ImageValidator(settings=self._settings)
        self._decoder = decoder or GpuPilDecoder(device_id=self._settings.gpu_device_id)
        self._preprocessor = preprocessor or TorchPreprocessor(
            device_id=self._settings.gpu_device_id
        )
        self._dali_decoder = dali_decoder or GpuDaliDecoder(
            device_id=self._settings.gpu_device_id,
            input_size=self._detector.input_size,
        )
        self._decoder_backend = decoder_backend

    @property
    def recognizer_name(self) -> str:
        return self._recognizer.name

    @property
    def recognizer_version(self) -> str:
        return self._recognizer.version

    def validate(self, image_bytes: bytes) -> ImageValidationResult:
        """Validate image bytes and return metadata."""
        return self._validator.validate(image_bytes)

    def enroll(self, image_bytes: bytes) -> list[EnrollOutput]:
        """Detect, align and embed every face in ``image_bytes``."""
        return self._encode_lazy_outputs(self._enroll_lazy(image_bytes))

    def enroll_lazy(self, image_bytes: bytes) -> list[LazyEnrollOutput]:
        """Detect, align and embed without JPEG encoding the crops."""
        return self._enroll_lazy(image_bytes)

    def _enroll_lazy(self, image_bytes: bytes) -> list[LazyEnrollOutput]:
        prepared = self._prepare(image_bytes)
        detections = self._detect(prepared)
        crops = self._align(prepared, detections)
        if crops.shape[0] == 0:
            return []

        embeddings = self._recognizer.embed(crops)
        return self._build_lazy_outputs(detections, crops, embeddings)

    def enroll_batch(self, image_bytes_list: list[bytes]) -> list[list[EnrollOutput]]:
        """Detect, align and embed every face in each image using packed batches.

        Uses the static TensorRT batch profiles (default ``[1, 8, 16, 32]``).
        Each chunk is zero-padded to the smallest profile that fits it, runs
        through the detector/recognizer once, and then the padding is stripped.
        When DALI is unavailable or ``decoder_backend`` is ``"pil"``, falls back
        to the single-image PIL path.
        """
        return [
            self._encode_lazy_outputs(lazy_list)
            for lazy_list in self.enroll_batch_lazy(image_bytes_list)
        ]

    def enroll_batch_lazy(
        self,
        image_bytes_list: list[bytes],
    ) -> list[list[LazyEnrollOutput]]:
        """Lazy variant of ``enroll_batch``; crops are raw tensors, not JPEG."""
        if not image_bytes_list:
            return []

        if self._decoder_backend == "pil":
            return self._enroll_batch_pil_lazy(image_bytes_list)

        try:
            return self._enroll_batch_dali_lazy(image_bytes_list)
        except RuntimeError:
            if self._decoder_backend == "dali":
                raise
            return self._enroll_batch_pil_lazy(image_bytes_list)

    def _chunk_by_profile(self, n: int) -> Iterator[tuple[int, int, int]]:
        """Yield ``(start, chunk_size, profile_size)`` chunks for ``n`` images."""
        profiles = tuple(sorted(self._settings.trt_batch_profiles or (1, 8, 16, 32)))
        max_profile = profiles[-1]
        start = 0
        while start < n:
            remaining = n - start
            chunk_size = min(remaining, max_profile)
            profile_size = next(p for p in profiles if p >= chunk_size)
            yield start, chunk_size, profile_size
            start += chunk_size

    @staticmethod
    def _pad_chunk(chunk: list[bytes], profile_size: int) -> list[bytes]:
        if len(chunk) >= profile_size:
            return chunk
        # Duplicate the last valid image for padding slots; the padding results
        # are discarded after inference.
        return chunk + [chunk[-1]] * (profile_size - len(chunk))

    def _enroll_batch_dali_lazy(
        self,
        image_bytes_list: list[bytes],
    ) -> list[list[LazyEnrollOutput]]:
        import torch

        outputs: list[list[LazyEnrollOutput]] = [[] for _ in image_bytes_list]

        for start, chunk_size, profile_size in self._chunk_by_profile(len(image_bytes_list)):
            chunk = image_bytes_list[start : start + chunk_size]
            padded = self._pad_chunk(chunk, profile_size)

            originals, model_inputs = self._dali_decoder.decode_batch(padded)
            # Original sizes come directly from decoded GPU tensors, avoiding a
            # second pass over the bytes by ImageValidator.
            original_sizes = [tuple(t.shape[1:]) for t in originals[:chunk_size]]
            original_sizes += [original_sizes[-1]] * (profile_size - chunk_size)

            detections = self._detector.detect_batch(
                model_inputs,
                original_sizes=original_sizes,
            )

            all_crops: list[torch.Tensor] = []
            crop_metadata: list[tuple[int, DetectionBatch]] = []

            for img_idx in range(chunk_size):
                dets = [d for d in detections if d.image_index == img_idx]
                if not dets:
                    continue

                det_batch = DetectionBatch(detections=tuple(dets), image_count=1)
                crop = self._aligner.align_crops(
                    originals[img_idx],
                    det_batch,
                    out_size=self._recognizer.input_size,
                )
                if crop.shape[0] == 0:
                    continue

                all_crops.append(crop)
                crop_metadata.append((img_idx, det_batch))

            if not all_crops:
                continue

            batched_crops = torch.cat(all_crops, dim=0)
            embeddings = self._recognizer.embed(batched_crops)

            offset = 0
            for img_idx, det_batch in crop_metadata:
                face_count = len(det_batch)
                face_crops = batched_crops[offset : offset + face_count]
                face_embeddings = embeddings.embeddings[offset : offset + face_count]
                offset += face_count

                outputs[start + img_idx] = self._build_lazy_outputs(
                    det_batch,
                    face_crops,
                    EmbeddingBatch(
                        embeddings=face_embeddings,
                        model_name=embeddings.model_name,
                        model_version=embeddings.model_version,
                        dimension=embeddings.dimension,
                    ),
                )

        return outputs

    def _enroll_batch_pil_lazy(
        self,
        image_bytes_list: list[bytes],
    ) -> list[list[LazyEnrollOutput]]:
        """Fallback path: run the single-image PIL pipeline for each input."""
        return [self._enroll_lazy(image_bytes) for image_bytes in image_bytes_list]

    def identify_prepare(self, image_bytes: bytes) -> list[QueryFaceOutput]:
        """Detect, align and embed every face for identification."""
        prepared = self._prepare(image_bytes)
        detections = self._detect(prepared)
        crops = self._align(prepared, detections)
        if crops.shape[0] == 0:
            return []

        embeddings = self._recognizer.embed(crops)
        return self._build_query_outputs(detections, embeddings)

    def _prepare(self, image_bytes: bytes) -> PreparedImage:
        validation = self._validator.validate(image_bytes)
        batch = self._decoder.decode_batch([image_bytes])
        original = batch[0]  # [3, H, W]

        model_input = self._preprocessor.resize_normalize(
            original.unsqueeze(0),
            size=self._detector.input_size,
            mean=(127.5, 127.5, 127.5),
            std=(128.0, 128.0, 128.0),
        )[0]

        return PreparedImage(
            original_tensor=original,
            model_input=model_input,
            original_size=(validation.height, validation.width),
            content_type=validation.content_type,
        )

    def _detect(self, prepared: PreparedImage) -> DetectionBatch:
        tensor = prepared.model_input.unsqueeze(0)  # [1, 3, S, S]
        return self._detector.detect_batch(
            tensor,
            original_sizes=[prepared.original_size],
        )

    def _align(
        self,
        prepared: PreparedImage,
        detections: DetectionBatch,
    ) -> torch.Tensor:
        return self._aligner.align_crops(
            prepared.original_tensor,
            detections,
            out_size=self._recognizer.input_size,
        )

    def _build_lazy_outputs(
        self,
        detections: DetectionBatch,
        crops: torch.Tensor,
        embeddings: EmbeddingBatch,
    ) -> list[LazyEnrollOutput]:
        outputs: list[LazyEnrollOutput] = []
        if hasattr(crops, "cpu"):
            crop_np = crops.detach().cpu().numpy().clip(0, 255).astype(np.uint8)
        else:
            crop_np = crops
        for idx, det in enumerate(detections):
            outputs.append(
                LazyEnrollOutput(
                    crop_tensor=crop_np[idx],
                    embedding=embeddings.embeddings[idx],
                    bbox=det.bbox,
                    landmarks=det.landmarks,
                    quality_score=det.score,
                    model_name=embeddings.model_name,
                    model_version=embeddings.model_version,
                    dimension=embeddings.dimension,
                )
            )
        return outputs

    @classmethod
    def _encode_lazy_outputs(
        cls,
        lazy_outputs: list[LazyEnrollOutput],
        quality: int = 85,
    ) -> list[EnrollOutput]:
        """Encode raw CHW crops to JPEG bytes on the caller thread."""
        outputs: list[EnrollOutput] = []
        for lazy in lazy_outputs:
            arr = lazy.crop_tensor.transpose(1, 2, 0)
            img = Image.fromarray(arr)
            buffer = cls._pil_to_bytes(img, quality=quality)
            outputs.append(
                EnrollOutput(
                    crop_bytes=buffer,
                    embedding=lazy.embedding,
                    bbox=lazy.bbox,
                    landmarks=lazy.landmarks,
                    quality_score=lazy.quality_score,
                    model_name=lazy.model_name,
                    model_version=lazy.model_version,
                    dimension=lazy.dimension,
                )
            )
        return outputs

    @classmethod
    def encode_crops_threaded(
        cls,
        lazy_outputs: list[LazyEnrollOutput],
        executor: concurrent.futures.ThreadPoolExecutor,
        quality: int = 85,
    ) -> list[EnrollOutput]:
        """Encode raw CHW crops to JPEG bytes using a thread pool.

        This lets CPU-bound JPEG encoding run in parallel with the next GPU
        inference batch. The list order is preserved.
        """

        def encode_one(lazy: LazyEnrollOutput) -> EnrollOutput:
            arr = lazy.crop_tensor.transpose(1, 2, 0)
            img = Image.fromarray(arr)
            buffer = cls._pil_to_bytes(img, quality=quality)
            return EnrollOutput(
                crop_bytes=buffer,
                embedding=lazy.embedding,
                bbox=lazy.bbox,
                landmarks=lazy.landmarks,
                quality_score=lazy.quality_score,
                model_name=lazy.model_name,
                model_version=lazy.model_version,
                dimension=lazy.dimension,
            )

        return list(executor.map(encode_one, lazy_outputs))

    def _build_query_outputs(
        self,
        detections: DetectionBatch,
        embeddings: EmbeddingBatch,
    ) -> list[QueryFaceOutput]:
        return [
            QueryFaceOutput(
                embedding=embeddings.embeddings[idx],
                bbox=det.bbox,
                landmarks=det.landmarks,
                quality_score=det.score,
            )
            for idx, det in enumerate(detections)
        ]

    @staticmethod
    def _pil_to_bytes(image: Image.Image, quality: int = 85) -> bytes:
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=quality)
        return buffer.getvalue()
