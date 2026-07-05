"""Tests for FacePipeline batch enrollment behaviour."""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pytest
import torch

from app.infrastructure.adapters.base import Detection, DetectionBatch, EmbeddingBatch
from app.infrastructure.adapters.pipelines import FacePipeline


def _detection(image_index: int) -> Detection:
    return Detection(
        image_index=image_index,
        bbox=(10.0, 10.0, 110.0, 110.0),
        score=0.99,
        landmarks=[(10.0, 10.0), (110.0, 10.0), (60.0, 60.0), (10.0, 110.0), (110.0, 110.0)],
    )


@pytest.fixture
def pipeline() -> FacePipeline:
    settings = MagicMock()
    settings.trt_batch_profiles = [1, 8, 16, 32]
    settings.gpu_device_id = 0
    settings.recognizer_mean = 127.5
    settings.recognizer_std = 127.5

    detector = MagicMock()
    detector.input_size = 320
    detector.detect_batch.return_value = DetectionBatch(
        detections=tuple(_detection(i) for i in range(4)),
        image_count=8,
    )

    aligner = MagicMock()
    aligner.align_crops.return_value = torch.rand(1, 3, 112, 112, dtype=torch.float32)

    recognizer = MagicMock()
    recognizer.input_size = 112
    recognizer.name = "arcface_w600k_r50"
    recognizer.version = "v1"
    recognizer.embed.return_value = EmbeddingBatch(
        embeddings=np.random.rand(4, 512).astype(np.float32),
        model_name="arcface_w600k_r50",
        model_version="v1",
        dimension=512,
    )

    validator = MagicMock()
    validator.validate.return_value.content_type = "image/jpeg"
    validator.validate.return_value.width = 480
    validator.validate.return_value.height = 640

    dali_decoder = MagicMock()
    originals = [torch.rand(3, 640, 480, dtype=torch.float32) for _ in range(8)]
    model_input = torch.rand(8, 3, 320, 320, dtype=torch.float32)
    dali_decoder.decode_batch.return_value = (originals, model_input)

    return FacePipeline(
        detector=detector,
        aligner=aligner,
        recognizer=recognizer,
        validator=validator,
        dali_decoder=dali_decoder,
        decoder_backend="dali",
        settings=settings,
    )


def test_enroll_batch_calls_detector_once_and_recognizer_once(pipeline: FacePipeline) -> None:
    """A 4-image chunk must produce one batched detector and one batched recognizer call."""
    image_bytes = [b"img1", b"img2", b"img3", b"img4"]

    outputs = pipeline.enroll_batch(image_bytes)

    assert len(outputs) == 4
    pipeline._detector.detect_batch.assert_called_once()
    assert pipeline._aligner.align_crops.call_count == 4
    pipeline._recognizer.embed.assert_called_once()

    recognizer_input = pipeline._recognizer.embed.call_args[0][0]
    assert recognizer_input.shape == (4, 3, 112, 112)
    assert recognizer_input.dtype == torch.float32
