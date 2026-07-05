"""Tests for the offline TensorRT engine builder script."""

from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest


def _fake_trt_module(tmp_path: Path) -> Any:
    """Return a fake tensorrt module whose builder produces deterministic bytes."""
    fake = MagicMock()
    fake.Logger.WARNING = 2
    fake.NetworkDefinitionCreationFlag.EXPLICIT_BATCH = 0
    fake.TensorIOMode.INPUT = 0
    fake.TensorIOMode.OUTPUT = 1
    fake.DataType.FLOAT = 0
    fake.BuilderFlag.FP16 = 1
    fake.MemoryPoolType.WORKSPACE = 0

    fake_builder = MagicMock()
    fake_builder.create_network.return_value = MagicMock()
    fake_builder.create_builder_config.return_value = MagicMock()
    fake_builder.create_optimization_profile.return_value = MagicMock()
    fake_builder.build_serialized_network.return_value = b"FAKE_ENGINE_BYTES"

    fake_runtime = MagicMock()
    fake.Runtime.return_value = fake_runtime

    fake.Logger.return_value = MagicMock()
    fake.Builder.return_value = fake_builder
    fake.OnnxParser.return_value = MagicMock()

    return fake


def test_build_engines_creates_expected_files(tmp_path: Path) -> None:
    """Builder must create {stem}.onnx_batch_{N}.plan files for each model and batch size."""
    from scripts import build_trt_engines

    models_dir = tmp_path / "models"
    models_dir.mkdir()
    output_dir = tmp_path / "engines"
    output_dir.mkdir()

    (models_dir / "scrfd_10g_320_batch.onnx").write_bytes(b"fake onnx")
    (models_dir / "arcface_w600k_r50_batch.onnx").write_bytes(b"fake onnx")

    build_trt_engines.trt = _fake_trt_module(tmp_path)  # type: ignore[attr-defined]

    build_trt_engines.main(
        [
            "--models-dir",
            str(models_dir),
            "--output-dir",
            str(output_dir),
            "--batch-sizes",
            "1",
        ]
    )

    assert (output_dir / "scrfd_10g_320_batch.onnx_batch_1.plan").exists()
    assert (output_dir / "arcface_w600k_r50_batch.onnx_batch_1.plan").exists()
    assert (
        output_dir / "scrfd_10g_320_batch.onnx_batch_1.plan"
    ).read_bytes() == b"FAKE_ENGINE_BYTES"


def test_build_engines_fp16_flag(tmp_path: Path) -> None:
    """Builder must enable FP16 when --fp16 is passed."""
    from scripts import build_trt_engines

    models_dir = tmp_path / "models"
    models_dir.mkdir()
    output_dir = tmp_path / "engines"
    output_dir.mkdir()
    (models_dir / "scrfd_10g_320_batch.onnx").write_bytes(b"fake onnx")
    (models_dir / "arcface_w600k_r50_batch.onnx").write_bytes(b"fake onnx")

    fake_trt = _fake_trt_module(tmp_path)
    build_trt_engines.trt = fake_trt  # type: ignore[attr-defined]

    build_trt_engines.main(
        [
            "--models-dir",
            str(models_dir),
            "--output-dir",
            str(output_dir),
            "--batch-sizes",
            "1",
            "--fp16",
        ]
    )

    config = fake_trt.Builder.return_value.create_builder_config.return_value
    config.set_flag.assert_any_call(fake_trt.BuilderFlag.FP16)
    assert config.set_flag.call_count == 2


def test_build_engines_missing_tensorrt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Builder must return a clear error if tensorrt is not installed."""
    from scripts import build_trt_engines

    build_trt_engines.trt = None  # type: ignore[attr-defined]

    stderr = StringIO()
    monkeypatch.setattr(sys, "stderr", stderr)

    models_dir = tmp_path / "models"
    models_dir.mkdir()
    output_dir = tmp_path / "engines"
    output_dir.mkdir()
    (models_dir / "scrfd_10g_320_batch.onnx").write_bytes(b"fake onnx")

    result = build_trt_engines.main(
        [
            "--models-dir",
            str(models_dir),
            "--output-dir",
            str(output_dir),
            "--batch-sizes",
            "1",
        ]
    )

    assert result == 1
    assert "tensorrt" in stderr.getvalue().lower()


def test_engine_file_name_matches_registry(tmp_path: Path) -> None:
    """Generated engine names must match ModelRegistry.trt_engine_path exactly."""
    from app.core.config import Settings
    from app.infrastructure.model_registry import ModelRegistry
    from scripts import build_trt_engines

    output_dir = tmp_path / "engines"
    output_dir.mkdir()

    settings = Settings(
        detector_model_name="scrfd_10g_320_batch.onnx",
        recognizer_model_name="arcface_w600k_r50_batch.onnx",
        trt_engine_dir=output_dir,
    )
    registry = ModelRegistry(settings)

    models_dir = tmp_path / "models"
    models_dir.mkdir()
    (models_dir / settings.detector_model_name).write_bytes(b"fake onnx")
    (models_dir / settings.recognizer_model_name).write_bytes(b"fake onnx")

    build_trt_engines.trt = _fake_trt_module(tmp_path)  # type: ignore[attr-defined]

    build_trt_engines.main(
        [
            "--models-dir",
            str(models_dir),
            "--output-dir",
            str(output_dir),
            "--batch-sizes",
            "1",
        ]
    )

    expected_detector = registry.trt_engine_path(registry.get_detector(), 1)
    assert expected_detector.exists()
    assert expected_detector.name == "scrfd_10g_320_batch.onnx_batch_1.plan"


def test_build_engine_directly(tmp_path: Path) -> None:
    """build_engine() must serialize a single engine for a given onnx path."""
    from scripts import build_trt_engines

    build_trt_engines.trt = _fake_trt_module(tmp_path)  # type: ignore[attr-defined]
    onnx_path = tmp_path / "model.onnx"
    onnx_path.write_bytes(b"fake onnx")
    output_path = tmp_path / "model.onnx_batch_4.plan"

    build_trt_engines.build_engine(onnx_path, output_path, batch_size=4, input_shape=(3, 320, 320))

    assert output_path.exists()
    assert output_path.read_bytes() == b"FAKE_ENGINE_BYTES"


def test_build_engine_workspace_mb(tmp_path: Path) -> None:
    """build_engine() must pass workspace_mb to the TensorRT memory pool limit."""
    from scripts import build_trt_engines

    fake_trt = _fake_trt_module(tmp_path)
    build_trt_engines.trt = fake_trt  # type: ignore[attr-defined]
    onnx_path = tmp_path / "model.onnx"
    onnx_path.write_bytes(b"fake onnx")
    output_path = tmp_path / "model.onnx_batch_1.plan"

    build_trt_engines.build_engine(
        onnx_path,
        output_path,
        batch_size=1,
        input_shape=(3, 320, 320),
        workspace_mb=2048,
    )

    config = fake_trt.Builder.return_value.create_builder_config.return_value
    config.set_memory_pool_limit.assert_called_once_with(
        fake_trt.MemoryPoolType.WORKSPACE, 2048 * 1024 * 1024
    )
