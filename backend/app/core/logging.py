"""Structured logging configuration."""

import logging
import sys


def configure_logging(level: str | None = None) -> None:
    """Configure the root logger with a standard format."""
    effective_level = (level or "INFO").upper()
    logging.basicConfig(
        level=effective_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
