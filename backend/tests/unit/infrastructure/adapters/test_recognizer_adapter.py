"""Unit tests for the TensorRT ArcFace recognizer adapter."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest
from numpy.typing import NDArray

from app.core.config import Settings
from app.infrastructure.adapters.base import EmbeddingBatch
from app.infrastructure.adapters.recognizer_adapter import RecognizerAdapter

torch = pytest.importorskip("torch")


@pytest.fixture
def settings(models_dir: Path) -> Settings:
    return Settings(
        models_dir=models_dir,
        recognizer_model_name="arcface_w600k_r50_batch.onnx",
        recognizer_embedding_dimension=512,
        recognizer_input_size=112,
        recognizer_mean=127.5,
        recognizer_std=127.5,
        recognizer_version="batch",
    )


@pytest.fixture
def models_dir() -> Path:
    repo_root = Path(__file__).resolve().parents[6]
    return repo_root / "artifacts" / "model_benchmarks" / "models"


@pytest.fixture
def adapter(settings: Settings) -> RecognizerAdapter:
    return RecognizerAdapter(settings=settings)


def _make_bgr_crop(size: int = 112) -> NDArray[np.uint8]:
    rng = np.random.default_rng(42)
    return rng.integers(0, 256, size=(size, size, 3), dtype=np.uint8)


def _make_rgb_tensor(n: int = 1, size: int = 112) -> torch.Tensor:  # type: ignore[name-defined]
    rng = np.random.default_rng(42)
    arr = rng.integers(0, 256, size=(n, size, size, 3), dtype=np.uint8)
    return torch.from_numpy(arr).permute(0, 3, 1, 2).to(torch.float32)


def _attach_mock_session(adapter: RecognizerAdapter, batch_size: int = 1) -> MagicMock:
    mock_session = MagicMock()
    adapter._sessions[batch_size] = mock_session
    return mock_session


def test_recognizer_returns_normalized_embeddings(adapter: RecognizerAdapter) -> None:
    mock_session = _attach_mock_session(adapter)
    raw = np.array([[3.0, 4.0] + [0.0] * 510], dtype=np.float32)
    mock_session.infer.return_value = [raw]

    tensor = _make_rgb_tensor(1)
    result = adapter.embed(tensor)

    assert isinstance(result, EmbeddingBatch)
    assert result.embeddings.shape == (1, 512)
    np.testing.assert_allclose(result.embeddings[0, :2], np.array([0.6, 0.8]))
    assert np.allclose(np.linalg.norm(result.embeddings, axis=1), 1.0)


def test_recognizer_batch_size_preserved(adapter: RecognizerAdapter) -> None:
    adapter._settings.trt_batch_profiles = (1, 2, 4, 8, 16, 32)
    n = 4
    mock_session = _attach_mock_session(adapter, batch_size=n)
    mock_session.infer.return_value = [
        np.tile(np.array([3.0, 4.0] + [0.0] * 510, dtype=np.float32), (n, 1))
    ]

    tensor = _make_rgb_tensor(n)
    result = adapter.embed(tensor)

    assert result.embeddings.shape == (n, 512)
    assert np.allclose(np.linalg.norm(result.embeddings, axis=1), 1.0)


def test_recognizer_passes_nchw_tensor(adapter: RecognizerAdapter) -> None:
    adapter._settings.trt_batch_profiles = (1, 2, 4, 8, 16, 32)
    mock_session = _attach_mock_session(adapter, batch_size=2)
    mock_session.infer.return_value = [np.zeros((2, 512), dtype=np.float32)]

    tensor = _make_rgb_tensor(2)
    adapter.embed(tensor)

    call_args = mock_session.infer.call_args
    input_tensor = call_args.args[0]

    assert input_tensor.shape == (2, 3, 112, 112)
    assert input_tensor.dtype == torch.float32


def test_recognizer_applies_rgb_normalization(adapter: RecognizerAdapter) -> None:
    mock_session = _attach_mock_session(adapter)
    mock_session.infer.return_value = [np.zeros((1, 512), dtype=np.float32)]

    red = torch.zeros((1, 3, 112, 112), dtype=torch.float32)
    red[:, 0, :, :] = 255.0  # red channel
    adapter.embed(red)

    input_tensor = mock_session.infer.call_args.args[0]
    mean = adapter._settings.recognizer_mean
    std = adapter._settings.recognizer_std
    np.testing.assert_allclose(input_tensor[0, 0, 0, 0].item(), (255.0 - mean) / std, rtol=1e-5)


def test_recognizer_raises_on_shape_mismatch(adapter: RecognizerAdapter) -> None:
    mock_session = _attach_mock_session(adapter)
    mock_session.infer.return_value = [np.zeros((1, 512), dtype=np.float32)]

    bad = torch.zeros((1, 3, 224, 224), dtype=torch.float32)
    with pytest.raises(ValueError, match="Recognizer expects"):
        adapter.embed(bad)


def test_recognizer_handles_empty_input(adapter: RecognizerAdapter) -> None:
    mock_session = _attach_mock_session(adapter)

    result = adapter.embed(torch.zeros((0, 3, 112, 112), dtype=torch.float32))

    assert result.embeddings.shape == (0, 512)
    mock_session.infer.assert_not_called()


def test_recognizer_handles_zero_norm_without_nan(adapter: RecognizerAdapter) -> None:
    mock_session = _attach_mock_session(adapter)
    mock_session.infer.return_value = [np.zeros((1, 512), dtype=np.float32)]

    tensor = _make_rgb_tensor(1)
    result = adapter.embed(tensor)

    assert result.embeddings.shape == (1, 512)
    assert np.allclose(result.embeddings, 0.0)
    assert not np.any(np.isnan(result.embeddings))


def test_recognizer_properties(adapter: RecognizerAdapter) -> None:
    assert adapter.embedding_dimension == 512
    assert adapter.input_size == 112
    assert adapter.version == "batch"
    assert "arcface" in adapter.name.lower()
