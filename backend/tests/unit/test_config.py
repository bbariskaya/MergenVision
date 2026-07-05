"""Unit tests for configuration."""

from app.core.config import Settings, get_settings


def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.app_name == "MergenVision"
    assert settings.environment == "local"
    assert settings.debug is True
    assert settings.database_url.startswith("postgresql+asyncpg://")


def test_get_settings_cached() -> None:
    first = get_settings()
    second = get_settings()
    assert first is second
