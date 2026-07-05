"""Unit tests for GpuDaliDecoder."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import torch


class _FakeTensorGPU:
    def __init__(self, tensor: torch.Tensor) -> None:
        self._tensor = tensor

    def as_tensor(self) -> _FakeTensorGPU:
        return self

    def __dlpack__(self, stream: object = None) -> object:
        import torch.utils.dlpack as torch_dlpack

        return torch_dlpack.to_dlpack(self._tensor)

    def toDlpack(self) -> object:  # noqa: N802
        import torch.utils.dlpack as torch_dlpack

        return torch_dlpack.to_dlpack(self._tensor)


class _FakeTensorList:
    def __init__(self, tensors: list[torch.Tensor]) -> None:
        self._tensors = tensors

    def __len__(self) -> int:
        return len(self._tensors)

    def __getitem__(self, index: int) -> _FakeTensorGPU:
        return _FakeTensorGPU(self._tensors[index])

    def as_tensor(self) -> _FakeTensorGPU:
        return _FakeTensorGPU(torch.stack(self._tensors))

    def toDlpack(self) -> object:  # noqa: N802
        import torch.utils.dlpack as torch_dlpack

        return torch_dlpack.to_dlpack(torch.stack(self._tensors))


def _build_fake_pipeline(
    originals: list[torch.Tensor],
    model_input: list[torch.Tensor],
):
    """Return a mock DALI pipeline that yields the two tensor lists."""
    pipeline = MagicMock()
    pipeline.run.return_value = (
        _FakeTensorList(originals),
        _FakeTensorList(model_input),
    )
    return pipeline


def test_decode_batch_raises_runtime_error_when_dali_not_installed() -> None:
    """CPU-only environments must trigger the PIL fallback path."""
    from app.infrastructure.adapters.gpu_dali_decoder import GpuDaliDecoder

    decoder = GpuDaliDecoder(device_id=0, input_size=320)

    with (
        patch.object(decoder, "_get_pipeline", side_effect=RuntimeError("no dali")),
        pytest.raises(RuntimeError, match="no dali"),
    ):
        decoder.decode_batch([b"fake-image"])


def test_decode_batch_returns_original_and_model_input() -> None:
    """Mocked DALI yields a list of variable-shape originals plus uniform detector input."""
    from app.infrastructure.adapters.gpu_dali_decoder import GpuDaliDecoder

    decoder = GpuDaliDecoder(device_id=0, input_size=320)
    # DALI returns [H, W, 3] uint8 originals; the decoder permutes/casts to [3, H, W] float.
    originals = [
        torch.randint(0, 255, (480, 640, 3), dtype=torch.uint8),
        torch.randint(0, 255, (250, 350, 3), dtype=torch.uint8),
    ]
    model_input = [
        torch.rand(3, 320, 320, dtype=torch.float32),
        torch.rand(3, 320, 320, dtype=torch.float32),
    ]

    with patch.object(
        decoder,
        "_get_pipeline",
        return_value=_build_fake_pipeline(originals, model_input),
    ):
        out_originals, out_model_input = decoder.decode_batch([b"a", b"b"])

    assert isinstance(out_originals, list)
    assert len(out_originals) == 2
    assert out_originals[0].shape == (3, 480, 640)
    assert out_originals[1].shape == (3, 250, 350)
    assert torch.allclose(out_originals[0], originals[0].permute(2, 0, 1).float())
    assert torch.allclose(out_originals[1], originals[1].permute(2, 0, 1).float())

    assert out_model_input.shape == (2, 3, 320, 320)
    assert torch.allclose(out_model_input, torch.stack(model_input))


def test_decode_batch_empty_input() -> None:
    """Empty input returns empty tensors without touching DALI."""

    from app.infrastructure.adapters.gpu_dali_decoder import GpuDaliDecoder

    decoder = GpuDaliDecoder(device_id=0, input_size=320)
    out_originals, out_model_input = decoder.decode_batch([])

    assert isinstance(out_originals, list)
    assert len(out_originals) == 0
    assert out_model_input.shape == (0, 3, 320, 320)
