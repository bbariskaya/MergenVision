#!/usr/bin/env python3
"""Benchmark face enrollment throughput on LFW.

Measures the ML pipeline phases used by ``FacePipeline.enroll_batch``:

    decode -> detect -> align -> recognize -> crop_encode

Persistence phases (upload, db_insert, qdrant_upsert) are not part of
``FacePipeline``; they are reported as ``N/A`` by default. Run the application
profile with real storage/repos attached to measure end-to-end persistence.

Usage::

    CUDA_VISIBLE_DEVICES=1 GPU_DEVICE_ID=0 \
        python scripts/benchmark_enrollment.py
"""

from __future__ import annotations

import argparse
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from app.core.config import Settings
from app.infrastructure.adapters.pipelines import FacePipeline

_F = TypeVar("_F", bound=Callable[..., Any])


def _lfw_image_paths(lfw_dir: Path, limit: int | None = None) -> list[Path]:
    paths = sorted(lfw_dir.rglob("*.jpg"))
    if not paths:
        raise RuntimeError(f"No *.jpg images found under {lfw_dir}")
    if limit:
        paths = paths[:limit]
    return paths


def _patch_timers(pipeline: FacePipeline) -> dict[str, float]:
    """Wrap ML methods and return an accumulator dict keyed by phase."""
    timers: dict[str, float] = {
        "decode": 0.0,
        "detect": 0.0,
        "align": 0.0,
        "recognize": 0.0,
        "crop_encode": 0.0,
    }

    def wrap(method: _F, key: str) -> _F:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            result = method(*args, **kwargs)
            timers[key] += time.perf_counter() - start
            return result

        return wrapper  # type: ignore[return-value]

    # Decode: whichever backend is active will be hit.
    pipeline._dali_decoder.decode_batch = wrap(pipeline._dali_decoder.decode_batch, "decode")
    pipeline._decoder.decode_batch = wrap(pipeline._decoder.decode_batch, "decode")

    pipeline._detector.detect_batch = wrap(pipeline._detector.detect_batch, "detect")
    pipeline._aligner.align_crops = wrap(pipeline._aligner.align_crops, "align")
    pipeline._recognizer.embed = wrap(pipeline._recognizer.embed, "recognize")
    pipeline._build_enroll_outputs = wrap(pipeline._build_enroll_outputs, "crop_encode")

    return timers


def _run_benchmark(pipeline: FacePipeline, image_bytes: list[bytes]) -> dict[str, Any]:
    timers = _patch_timers(pipeline)

    total_start = time.perf_counter()
    outputs = pipeline.enroll_batch(image_bytes)
    total_elapsed = time.perf_counter() - total_start
    face_count = sum(len(face_list) for face_list in outputs)

    return {
        "images": len(image_bytes),
        "faces": face_count,
        "total_seconds": total_elapsed,
        "timers": timers,
    }


def _print_report(metrics: dict[str, Any]) -> None:
    images = metrics["images"]
    faces = metrics["faces"]
    total = metrics["total_seconds"]
    timers = metrics["timers"]

    print("\n=== LFW Enrollment Benchmark ===")
    print(f"images          : {images}")
    print(f"faces           : {faces}")
    print(f"total_seconds   : {total:.3f}")
    print(f"img/s           : {images / total:.1f}")
    print(f"face/s          : {faces / total:.1f}")
    print("\n--- ML pipeline phase times (seconds) ---")
    print(f"decode          : {timers['decode']:.3f}")
    print(f"detect          : {timers['detect']:.3f}")
    print(f"align           : {timers['align']:.3f}")
    print(f"recognize       : {timers['recognize']:.3f}")
    print(f"crop_encode     : {timers['crop_encode']:.3f}")
    print("upload          : N/A (requires persistence wiring)")
    print("db_insert       : N/A (requires persistence wiring)")
    print("qdrant_upsert   : N/A (requires persistence wiring)")

    ml_sum = sum(timers[k] for k in ("decode", "detect", "align", "recognize", "crop_encode"))
    print(f"\nml_phase_sum    : {ml_sum:.3f} ({100 * ml_sum / total:.1f}% of total)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark LFW enrollment throughput")
    parser.add_argument(
        "--lfw-dir",
        type=Path,
        default=Path("/home/user/MergenVision/test_datasets/lfw/lfw-deepfunneled"),
        help="Directory containing LFW images",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N images",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=8,
        help="Number of warmup images before timing",
    )
    parser.add_argument(
        "--decoder-backend",
        choices=("auto", "dali", "pil"),
        default="auto",
        help="Decoder backend to use",
    )
    parser.add_argument(
        "--gpu-device-id",
        type=int,
        default=None,
        help="GPU device id (overrides settings)",
    )
    args = parser.parse_args()

    settings_kwargs: dict[str, Any] = {"decoder_backend": args.decoder_backend}
    if args.gpu_device_id is not None:
        settings_kwargs["gpu_device_id"] = args.gpu_device_id
    settings = Settings(**settings_kwargs)

    paths = _lfw_image_paths(args.lfw_dir, args.limit)
    image_bytes = [path.read_bytes() for path in paths]

    pipeline = FacePipeline(settings=settings, decoder_backend=args.decoder_backend)

    # Warmup to amortize model load / CUDA init.
    if args.warmup and image_bytes:
        pipeline.enroll_batch(image_bytes[: args.warmup])

    metrics = _run_benchmark(pipeline, image_bytes)
    _print_report(metrics)


if __name__ == "__main__":
    main()
