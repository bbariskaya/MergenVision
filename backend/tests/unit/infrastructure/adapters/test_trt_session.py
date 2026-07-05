"""Tests for the TensorRT inference session wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
import torch

from app.infrastructure.adapters.trt_session import TrtInferenceSession


def _fake_engine_bytes(tmp_path: Path) -> Path:
    path = tmp_path / "model.onnx_batch_1.plan"
    path.write_bytes(b"serialized_engine")
    return path


def _fake_trt_module() -> Any:
    fake = MagicMock()
    fake.Logger.WARNING = 2
    fake.TensorIOMode.INPUT = 0
    fake.TensorIOMode.OUTPUT = 1

    fake_engine = MagicMock()
    fake_engine.num_io_tensors = 2
    fake_engine.get_tensor_name.side_effect = lambda i: ["input", "output"][i]
    fake_engine.get_tensor_mode.side_effect = lambda name: (
        fake.TensorIOMode.INPUT if name == "input" else fake.TensorIOMode.OUTPUT
    )

    fake_context = MagicMock()
    fake_runtime = MagicMock()
    fake_runtime.deserialize_cuda_engine.return_value = fake_engine
    fake.Runtime.return_value = fake_runtime
    fake_engine.create_execution_context.return_value = fake_context

    fake.Logger.return_value = MagicMock()
    return fake


def test_load_raises_on_cpu(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """If CUDA is unavailable, load() must raise a clear, actionable error."""
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)

    path = _fake_engine_bytes(tmp_path)
    session = TrtInferenceSession(path)

    with pytest.raises(RuntimeError, match="CUDA"):
        session.load()


def test_load_succeeds_with_cuda_and_tensorrt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With CUDA available and a mocked TensorRT module, load() initializes the session."""
    from app.infrastructure.adapters import trt_session

    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "Stream", MagicMock())
    trt_session.trt = _fake_trt_module()  # type: ignore[attr-defined]

    path = _fake_engine_bytes(tmp_path)
    session = TrtInferenceSession(path)
    session.load()

    assert session._context is not None
    assert session._stream is not None
    assert session._input_name == "input"
    assert session._output_names == ["output"]
