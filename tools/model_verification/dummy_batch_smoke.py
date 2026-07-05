#!/usr/bin/env python3
import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import onnxruntime as ort

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SIZES = [1, 4, 8, 16, 32]
WIDTH_MAP = {
    "scrfd_10g_320": 320,
    "arcface_w600k_r50": 112,
    "face_recognition_sface_2021dec": 112,
    "edgeface_xxs": 112,
    "face_detection_yunet_2026may": 640,
}


def infer_width(model_path: Path) -> int:
    name = model_path.stem
    for key, width in WIDTH_MAP.items():
        if key in name:
            return width
    raise ValueError(f"Cannot infer input spatial size for {model_path}; use --size")


def run_batch(session, batch_size: int, width: int, seed: int) -> dict:
    rng = np.random.default_rng(seed=seed + batch_size)
    x = rng.random(size=(batch_size, 3, width, width)).astype(np.float32)
    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: x})
    return {
        "input_shape": list(x.shape),
        "output_shapes": [list(o.shape) for o in outputs],
        "first_output_shape": list(outputs[0].shape) if outputs else None,
    }


def benchmark(session, batch_size: int, width: int, runs: int, warmup: int, seed: int) -> dict:
    for _ in range(warmup):
        run_batch(session, batch_size, width, seed)

    timings = []
    for _ in range(runs):
        t0 = time.perf_counter()
        snap = run_batch(session, batch_size, width, seed)
        t1 = time.perf_counter()
        timings.append((t1 - t0) * 1000.0)

    timings.sort()
    mid = len(timings) // 2
    median = timings[mid] if len(timings) % 2 == 1 else (timings[mid - 1] + timings[mid]) / 2.0
    return {
        "batch_size": batch_size,
        "input_shape": snap["input_shape"],
        "first_output_shape": snap["first_output_shape"],
        "all_output_shapes": snap["output_shapes"],
        "median_ms": round(median, 3),
        "min_ms": round(timings[0], 3),
        "max_ms": round(timings[-1], 3),
        "runs": runs,
        "warmup": warmup,
        "status": "ok",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", required=True, type=Path)
    parser.add_argument("--provider", required=True, choices=["CPU", "CUDA"])
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--batch_sizes", default=",".join(str(s) for s in DEFAULT_SIZES))
    parser.add_argument("--size", type=int, default=None)
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    model_path = args.model_path
    if not model_path.is_absolute():
        model_path = REPO_ROOT / model_path

    provider = args.provider
    providers = [f"{provider}ExecutionProvider"]
    width = args.size if args.size else infer_width(model_path)
    batch_sizes = [int(s.strip()) for s in args.batch_sizes.split(",") if s.strip()]

    environment = {
        "onnxruntime_version": ort.__version__,
        "available_providers": ort.get_available_providers(),
        "requested_provider": provider,
        "providers_argument": providers,
        "model_file": str(model_path.relative_to(REPO_ROOT)),
        "input_spatial_size": width,
        "batch_sizes": batch_sizes,
        "runs_per_size": args.runs,
        "warmup": args.warmup,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    result = {
        "environment": environment,
        "results": [],
        "overall_status": "pending",
    }

    try:
        session = ort.InferenceSession(str(model_path), providers=providers)
    except Exception as exc:
        result["overall_status"] = f"{provider.lower()}_provider_unavailable"
        result["error"] = f"{type(exc).__name__}: {exc}"
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps({"ok": False, "provider": provider, "error": result["error"], "output": str(args.output.relative_to(REPO_ROOT) if args.output.is_absolute() else args.output)}, indent=2))
        return 0 if provider == "CUDA" else 1

    result["actual_providers"] = session.get_providers()
    requested_str = f"{provider}ExecutionProvider"
    if requested_str not in session.get_providers():
        result["overall_status"] = f"{provider.lower()}_provider_unavailable"
        result["error"] = f"Requested {requested_str} but ORT selected {session.get_providers()}; CUDA runtime shared library (libcudnn.so.9) could not be loaded."
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps({"ok": False, "provider": provider, "error": result["error"], "output": str(args.output.relative_to(REPO_ROOT) if args.output.is_absolute() else args.output)}, indent=2))
        return 0 if provider == "CUDA" else 1

    for batch_size in batch_sizes:
        try:
            entry = benchmark(session, batch_size, width, args.runs, args.warmup, args.seed)
        except Exception as exc:
            entry = {
                "batch_size": batch_size,
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            }
        result["results"].append(entry)

    failed = [r for r in result["results"] if r.get("status") != "ok"]
    result["overall_status"] = "ok" if not failed else "partial"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"ok": not failed, "provider": provider, "sizes_tested": len(result["results"]), "failed": len(failed), "output": str(args.output.relative_to(REPO_ROOT) if args.output.is_absolute() else args.output)}, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
