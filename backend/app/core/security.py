"""Security helpers for request tracing, safe logging, and PII handling."""

import hashlib
import hmac

from fastapi import Request

from app.core.config import get_settings
from app.core.ids import new_uuid7, uuid7_to_str


def get_or_create_request_id(request: Request) -> str:
    """Return the client request ID if present and safe; otherwise generate a new UUIDv7."""
    header = request.headers.get("x-request-id")
    if header and isinstance(header, str) and 0 < len(header) <= 64:
        return header.strip()
    return uuid7_to_str(new_uuid7())


def sanitize_header_value(value: str | None, max_len: int = 100) -> str:
    """Return a CRLF-free, length-limited string suitable for logging."""
    if not value:
        return ""
    return value.strip()[:max_len].replace("\n", "").replace("\r", "")


def hash_national_id(national_id: str) -> str:
    """Return a deterministic HMAC-SHA256 hash of a national ID.

    Uses a server-side pepper to mitigate brute-force lookup of national IDs
    from known values. The hash is deterministic so duplicates can be detected.
    """
    normalized = national_id.strip()
    pepper = get_settings().national_id_pepper.encode("utf-8")
    return hmac.new(pepper, normalized.encode("utf-8"), hashlib.sha256).hexdigest()


def mask_national_id(national_id: str | None) -> str | None:
    """Mask a national ID, keeping only the last four characters."""
    if national_id is None or len(national_id) < 4:
        return None
    return "*" * (len(national_id) - 4) + national_id[-4:]
