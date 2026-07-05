"""Environment-driven application settings."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "MergenVision"
    app_version: str = "0.1.0"
    environment: str = "local"
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/mergenvision"
    postgres_pool_size: int = 5
    postgres_max_overflow: int = 10

    # Logging
    log_level: str = "INFO"

    # Object storage
    minio_url: str = "localhost:9000"
    minio_public_url: str | None = None
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket_people_photos: str = "people-photos"
    minio_bucket_face_crops: str = "face-crops"
    minio_bucket_query_images: str = "query-images"
    minio_url_expiry_seconds: int = 3600

    # Vector store
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection_prefix: str = "face_samples"

    # Model files
    models_dir: Path = (
        Path(__file__).resolve().parents[3] / "artifacts" / "model_benchmarks" / "models"
    )
    detector_model_name: str = "scrfd_10g_320_batch.onnx"
    recognizer_model_name: str = "arcface_w600k_r50_batch.onnx"

    detector_input_size: int = 320
    detector_confidence_threshold: float = 0.5
    detector_nms_threshold: float = 0.4

    recognizer_input_size: int = 112
    recognizer_embedding_dimension: int = 512
    recognizer_mean: float = 127.5
    recognizer_std: float = 127.5
    recognizer_version: str = "batch"

    # TensorRT
    trt_engine_dir: Path = Path(__file__).resolve().parents[3] / "artifacts" / "trt_engines"
    trt_batch_profiles: tuple[int, ...] = (1, 8, 16, 32)
    trt_use_fp16: bool = True
    trt_workspace_mb: int = 4096
    gpu_device_id: int = 0

    # Business rules
    matched_threshold: float = 0.6
    possible_match_threshold: float = 0.4
    max_upload_bytes: int = 10 * 1024 * 1024  # 10 MiB
    store_query_images: bool = True

    # Identification defaults
    default_top_k: int = 5
    max_top_k: int = 20

    # National ID
    national_id_pepper: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached, globally shared settings instance."""
    return Settings()
