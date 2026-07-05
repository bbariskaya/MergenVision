"""Tests for the GPU/CPU PIL-based image decoder."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
import torch
from PIL import Image


def _rgb_bytes(width: int, height: int, color: tuple[int, int, int] = (42, 84, 126)) -> bytes:
    img = Image.new("RGB", (width, height), color)
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()


def test_decodes_single_image_to_chw_tensor() -> None:
    """A single JPEG byte string decodes into [1, 3, H, W]."""
    from app.infrastructure.adapters.gpu_pil_decoder import GpuPilDecoder

    decoder = GpuPilDecoder(device_id=0)
    tensor = decoder.decode_batch([_rgb_bytes(80, 60)])

    assert tensor.shape == (1, 3, 60, 80)
    assert tensor.dtype == torch.float32
    assert tensor[0, :, 0, 0].tolist() == pytest.approx([42.0, 84.0, 126.0], abs=3.0)


def test_decodes_multiple_images() -> None:
    """A batch of same-size images decodes into [N, 3, H, W]."""
    from app.infrastructure.adapters.gpu_pil_decoder import GpuPilDecoder

    decoder = GpuPilDecoder(device_id=0)
    tensor = decoder.decode_batch(
        [_rgb_bytes(80, 60, (255, 0, 0)), _rgb_bytes(80, 60, (0, 255, 0))]
    )

    assert tensor.shape == (2, 3, 60, 80)
    assert tensor[0, :, 0, 0].tolist() == pytest.approx([255.0, 0.0, 0.0], abs=3.0)
    assert tensor[1, :, 0, 0].tolist() == pytest.approx([0.0, 255.0, 0.0], abs=3.0)


def test_runs_without_cuda(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Decoder must fall back to CPU when CUDA is unavailable."""
    from app.infrastructure.adapters.gpu_pil_decoder import GpuPilDecoder

    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)

    decoder = GpuPilDecoder(device_id=0)
    tensor = decoder.decode_batch([_rgb_bytes(10, 10)])

    assert tensor.device.type == "cpu"


def test_load_from_path(tmp_path: Path) -> None:
    """decode_batch_from_paths reads bytes from disk and delegates to decode_batch."""
    from app.infrastructure.adapters.gpu_pil_decoder import GpuPilDecoder

    path = tmp_path / "image.jpg"
    path.write_bytes(_rgb_bytes(20, 20))

    decoder = GpuPilDecoder(device_id=0)
    tensor = decoder.decode_batch_from_paths([str(path)])

    assert tensor.shape == (1, 3, 20, 20)
