"""Offline TensorRT engine builder for SCRFD and ArcFace ONNX models."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import tensorrt as trt
except Exception:  # pragma: no cover - TensorRT may not be installed on CPU-only hosts.
    trt = None

MODELS = [
    ("scrfd_10g_320_batch.onnx", (3, 320, 320)),
    ("arcface_w600k_r50_batch.onnx", (3, 112, 112)),
]


def build_engine(
    onnx_path: Path,
    output_path: Path,
    batch_size: int,
    input_shape: tuple[int, int, int],
    fp16: bool = False,
    workspace_mb: int = 4096,
) -> None:
    """Build a serialized TensorRT engine plan for one static batch size."""
    if trt is None:
        raise RuntimeError(
            "TensorRT is not installed. Install tensorrt and run on a CUDA-capable machine."
        )

    logger = trt.Logger(trt.Logger.WARNING)
    builder = trt.Builder(logger)
    network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
    parser = trt.OnnxParser(network, logger)
    with open(onnx_path, "rb") as f:
        if not parser.parse(f.read()):
            errors = [parser.get_error(i) for i in range(parser.num_errors)]
            raise RuntimeError(f"ONNX parse failed for {onnx_path}: {errors}")

    config = builder.create_builder_config()
    config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, workspace_mb * 1024 * 1024)
    if fp16:
        config.set_flag(trt.BuilderFlag.FP16)

    input_tensor = network.get_input(0)
    shape = (batch_size, *input_shape)
    profile = builder.create_optimization_profile()
    profile.set_shape(input_tensor.name, min=shape, opt=shape, max=shape)
    config.add_optimization_profile(profile)

    serialized = builder.build_serialized_network(network, config)
    if serialized is None:
        raise RuntimeError(f"TensorRT engine build failed for {onnx_path} batch={batch_size}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(serialized)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Build static-batch TensorRT engines from ONNX models."
    )
    parser.add_argument(
        "--models-dir",
        type=Path,
        required=True,
        help="Directory containing the ONNX model files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory where serialized .plan engine files are written.",
    )
    parser.add_argument(
        "--batch-sizes",
        type=int,
        nargs="+",
        default=[1, 8, 16, 32],
        help="Static batch sizes to build engines for.",
    )
    parser.add_argument(
        "--fp16",
        action="store_true",
        help="Enable FP16 precision in addition to FP32.",
    )
    parser.add_argument(
        "--workspace-mb",
        type=int,
        default=4096,
        help="GPU workspace size in MiB for engine builds.",
    )
    args = parser.parse_args(argv)

    if trt is None:
        print(
            "TensorRT is not installed. Install tensorrt and run on a CUDA-capable machine.",
            file=sys.stderr,
        )
        return 1

    for model_name, input_shape in MODELS:
        onnx_path = args.models_dir / model_name
        if not onnx_path.exists():
            print(f"ONNX model not found: {onnx_path}", file=sys.stderr)
            return 1
        stem = Path(model_name).stem
        for batch_size in args.batch_sizes:
            output_name = f"{stem}.onnx_batch_{batch_size}.plan"
            output_path = args.output_dir / output_name
            build_engine(
                onnx_path,
                output_path,
                batch_size,
                input_shape,
                args.fp16,
                args.workspace_mb,
            )
            print(f"Built {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
