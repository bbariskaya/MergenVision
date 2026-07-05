"""Profile FacePipeline inference in isolation (no DB/MinIO/Qdrant)."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

script_dir = Path(__file__).resolve().parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import get_settings  # noqa: E402
from app.infrastructure.adapters.pipelines import FacePipeline  # noqa: E402
from app.infrastructure.adapters.trt_session import TrtInferenceSession  # noqa: E402
from app.infrastructure.model_registry import get_model_registry  # noqa: E402


def main() -> None:
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://mergen:mergen@localhost:5433/mergenvision"
    os.environ["QDRANT_URL"] = "http://localhost:6334"
    os.environ["MINIO_URL"] = "localhost:9002"
    os.environ["MINIO_ACCESS_KEY"] = "minioadmin"
    os.environ["MINIO_SECRET_KEY"] = "minioadmin"
    os.environ["MINIO_SECURE"] = "false"
    os.environ["TRT_ENGINE_DIR"] = "/home/user/MergenVision/artifacts/trt_engines"
    os.environ["MODELS_DIR"] = "/home/user/MergenVision/artifacts/model_benchmarks/models"
    os.environ["GPU_DEVICE_ID"] = "0"

    get_settings.cache_clear()
    settings = get_settings()
    print(f"TRT engine dir: {settings.trt_engine_dir}")
    print(f"Models dir: {settings.models_dir}")

    dataset = Path("/home/user/MergenVision/testdatasets/img_align_celeba/img_align_celeba")
    image_paths = sorted(dataset.glob("*.jpg"))[:100]
    print(f"Images: {len(image_paths)}")

    # --- raw engine load time ---
    registry = get_model_registry(settings)
    det_info = registry.get_detector()
    rec_info = registry.get_recognizer()
    det_path = registry.trt_engine_path(det_info, 32)
    rec_path = registry.trt_engine_path(rec_info, 32)
    print(f"Detector engine: {det_path}")
    print(f"Recognizer engine: {rec_path}")

    t0 = time.perf_counter()
    det_session = TrtInferenceSession(det_path)
    det_session.load()
    t1 = time.perf_counter()
    rec_session = TrtInferenceSession(rec_path)
    rec_session.load()
    t2 = time.perf_counter()
    print(f"Engine deserialize - detector: {t1 - t0:.2f}s, recognizer: {t2 - t1:.2f}s")

    # --- FacePipeline init ---
    t0 = time.perf_counter()
    pipeline = FacePipeline(settings=settings, decoder_backend="dali")
    t1 = time.perf_counter()
    print(f"FacePipeline init: {t1 - t0:.2f}s")

    # --- read bytes ---
    t0 = time.perf_counter()
    image_bytes = [p.read_bytes() for p in image_paths]
    t1 = time.perf_counter()
    print(f"Read bytes: {t1 - t0:.2f}s")

    # --- warmup batch (10) ---
    t0 = time.perf_counter()
    _ = pipeline.enroll_batch(image_bytes[:10])
    t1 = time.perf_counter()
    print(f"Warmup 10 images: {t1 - t0:.2f}s ({10 / (t1 - t0):.1f} img/s)")

    # --- full batch (100) ---
    t0 = time.perf_counter()
    outputs = pipeline.enroll_batch(image_bytes)
    t1 = time.perf_counter()
    total_faces = sum(len(o) for o in outputs)
    elapsed = t1 - t0
    print(f"Full 100 images: {elapsed:.2f}s ({100 / elapsed:.1f} img/s)")
    print(f"Faces detected: {total_faces}")


if __name__ == "__main__":
    main()
