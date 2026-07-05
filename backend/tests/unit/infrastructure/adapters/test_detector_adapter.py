"""SCRFD detector adapter unit tests for the TensorRT/torch interface."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import torch


@dataclass(frozen=True)
class _ModelInfo:
    name: str
    version: str
    local_path: Path
    input_size: int | None
    output_dim: int | None


class _FakeRegistry:
    def __init__(self) -> None:
        self.detector = _ModelInfo(
            name="scrfd_10g_320_batch",
            version="batch",
            local_path=Path("x.onnx"),
            input_size=320,
            output_dim=None,
        )

    def get_detector(self) -> _ModelInfo:
        return self.detector

    def trt_engine_path(self, model_info: _ModelInfo, batch_size: int) -> Path:
        return Path(f"{model_info.name}.onnx_batch_{batch_size}.plan")


class _FakeSession:
    def __init__(self, outputs: list[torch.Tensor]) -> None:
        self._outputs = outputs

    def infer(self, tensor: torch.Tensor) -> list[torch.Tensor]:
        return [out.clone() for out in self._outputs]


def _stride_totals(input_size: int = 320, num_anchors: int = 2) -> dict[int, int]:
    return {stride: (input_size // stride) ** 2 * num_anchors for stride in (8, 16, 32)}


def _empty_outputs(batch_size: int) -> list[torch.Tensor]:
    totals = _stride_totals()
    return [
        torch.zeros((batch_size, totals[8], 1)),
        torch.zeros((batch_size, totals[16], 1)),
        torch.zeros((batch_size, totals[32], 1)),
        torch.zeros((batch_size, totals[8], 4)),
        torch.zeros((batch_size, totals[16], 4)),
        torch.zeros((batch_size, totals[32], 4)),
        torch.zeros((batch_size, totals[8], 10)),
        torch.zeros((batch_size, totals[16], 10)),
        torch.zeros((batch_size, totals[32], 10)),
    ]


def _stride_index(stride: int) -> int:
    return {8: 0, 16: 1, 32: 2}[stride]


def _set_positive(
    outputs: list[torch.Tensor],
    batch_index: int,
    anchor_index: int,
    stride: int,
    score: float,
    bbox: tuple[float, float, float, float],
    landmarks: list[tuple[float, float]],
) -> None:
    """Fill one anchor so it decodes to the given model-space bbox/landmarks."""
    si = _stride_index(stride)
    score_offset = si
    bbox_offset = 3 + si
    kps_offset = 6 + si

    outputs[score_offset][batch_index, anchor_index, 0] = score

    cx = (anchor_index // 2 % (320 // stride)) * stride
    cy = (anchor_index // 2 // (320 // stride)) * stride
    x1, y1, x2, y2 = bbox
    outputs[bbox_offset][batch_index, anchor_index] = torch.tensor(
        [
            (cx - x1) / stride,
            (cy - y1) / stride,
            (x2 - cx) / stride,
            (y2 - cy) / stride,
        ],
        dtype=outputs[bbox_offset].dtype,
    )

    kps = []
    for lx, ly in landmarks:
        kps.extend([(lx - cx) / stride, (ly - cy) / stride])
    outputs[kps_offset][batch_index, anchor_index] = torch.tensor(
        kps, dtype=outputs[kps_offset].dtype
    )


@pytest.fixture
def adapter(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Build a DetectorAdapter with a fake registry and inject test fixtures."""
    from app.core.config import Settings
    from app.infrastructure.adapters.detector_adapter import DetectorAdapter

    settings = Settings(
        detector_confidence_threshold=0.5,
        detector_nms_threshold=0.4,
        trt_batch_profiles=(1, 8, 16, 32),
    )
    registry = _FakeRegistry()
    instance = DetectorAdapter(registry=registry, settings=settings)  # type: ignore[arg-type]
    return instance


def test_detect_empty_input(adapter: Any) -> None:
    """An empty batch must return an empty DetectionBatch."""
    import torch

    images = torch.zeros((0, 3, 320, 320), dtype=torch.float32)
    batch = adapter.detect_batch(images)

    assert batch.image_count == 0
    assert len(batch) == 0
    assert batch.by_image == {}


def test_detect_single_face(adapter: Any) -> None:
    """A single positive anchor must produce one Detection."""
    import torch

    outputs = _empty_outputs(1)
    _set_positive(
        outputs,
        batch_index=0,
        anchor_index=0,
        stride=32,
        score=0.9,
        bbox=(10.0, 10.0, 30.0, 30.0),
        landmarks=[(15.0, 15.0), (20.0, 15.0), (18.0, 22.0), (14.0, 28.0), (24.0, 28.0)],
    )
    adapter._sessions[1] = _FakeSession(outputs)

    images = torch.zeros((1, 3, 320, 320), dtype=torch.float32)
    batch = adapter.detect_batch(images)

    assert len(batch) == 1
    det = batch.by_image[0][0]
    assert det.bbox == pytest.approx((10.0, 10.0, 30.0, 30.0))
    assert det.score == pytest.approx(0.9)
    assert len(det.landmarks) == 5


def test_detect_multiple_images(adapter: Any) -> None:
    """Each image in the batch should receive its own detection."""
    import torch

    outputs = _empty_outputs(2)
    for img_idx in range(2):
        _set_positive(
            outputs,
            batch_index=img_idx,
            anchor_index=0,
            stride=32,
            score=0.9,
            bbox=(10.0, 10.0, 30.0, 30.0),
            landmarks=[(15.0, 15.0), (20.0, 15.0), (18.0, 22.0), (14.0, 28.0), (24.0, 28.0)],
        )
    adapter._sessions[8] = _FakeSession(outputs)

    images = torch.zeros((2, 3, 320, 320), dtype=torch.float32)
    batch = adapter.detect_batch(images, original_sizes=[(320, 320), (320, 320)])

    assert len(batch.by_image[0]) == 1
    assert len(batch.by_image[1]) == 1
    assert batch.by_image[0][0].image_index == 0
    assert batch.by_image[1][0].image_index == 1


def test_detect_filters_by_score_threshold(adapter: Any) -> None:
    """Detections below the configured confidence threshold must be dropped."""
    import torch

    outputs = _empty_outputs(1)
    _set_positive(
        outputs,
        batch_index=0,
        anchor_index=0,
        stride=32,
        score=0.2,
        bbox=(10.0, 10.0, 30.0, 30.0),
        landmarks=[(15.0, 15.0)] * 5,
    )
    adapter._sessions[1] = _FakeSession(outputs)

    images = torch.zeros((1, 3, 320, 320), dtype=torch.float32)
    batch = adapter.detect_batch(images)

    assert len(batch) == 0


def test_detect_applies_nms(adapter: Any) -> None:
    """Two overlapping detections must be suppressed to one."""
    import torch

    outputs = _empty_outputs(1)
    _set_positive(
        outputs,
        batch_index=0,
        anchor_index=0,
        stride=32,
        score=0.9,
        bbox=(10.0, 10.0, 30.0, 30.0),
        landmarks=[(15.0, 15.0), (20.0, 15.0), (18.0, 22.0), (14.0, 28.0), (24.0, 28.0)],
    )
    _set_positive(
        outputs,
        batch_index=0,
        anchor_index=1,
        stride=32,
        score=0.7,
        bbox=(10.0, 10.0, 30.0, 30.0),
        landmarks=[(15.0, 15.0), (20.0, 15.0), (18.0, 22.0), (14.0, 28.0), (24.0, 28.0)],
    )
    adapter._sessions[1] = _FakeSession(outputs)

    images = torch.zeros((1, 3, 320, 320), dtype=torch.float32)
    batch = adapter.detect_batch(images)

    assert len(batch) == 1
    assert batch.by_image[0][0].score == pytest.approx(0.9)


def test_detect_scales_to_original_size(adapter: Any) -> None:
    """Detected coordinates must be scaled back to original image size."""
    import torch

    outputs = _empty_outputs(1)
    _set_positive(
        outputs,
        batch_index=0,
        anchor_index=0,
        stride=32,
        score=0.9,
        bbox=(10.0, 10.0, 30.0, 30.0),
        landmarks=[(15.0, 15.0), (20.0, 15.0), (18.0, 22.0), (14.0, 28.0), (24.0, 28.0)],
    )
    adapter._sessions[1] = _FakeSession(outputs)

    images = torch.zeros((1, 3, 320, 320), dtype=torch.float32)
    batch = adapter.detect_batch(images, original_sizes=[(640, 480)])

    det = batch.by_image[0][0]
    scale = min(320 / 640, 320 / 480)
    expected_bbox = tuple(v / scale for v in (10.0, 10.0, 30.0, 30.0))
    assert det.bbox == pytest.approx(expected_bbox, rel=1e-4)
    assert det.landmarks[0] == pytest.approx((15.0 / scale, 15.0 / scale), rel=1e-4)
