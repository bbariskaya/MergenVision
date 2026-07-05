"""UUIDv7 identifier generation compatible with Python 3.12."""

import secrets
import time
import uuid


def new_uuid7() -> uuid.UUID:
    """Generate a new UUIDv7 using the current timestamp and random bytes."""
    timestamp_ms = int(time.time() * 1000) & 0xFFFFFFFFFFFF

    # 74 random bits split into rand_a (12 bits) and rand_b (62 bits).
    rand_bits = secrets.randbits(74)
    rand_a = (rand_bits >> 62) & 0xFFF
    rand_b = rand_bits & 0x3FFFFFFFFFFFFFFF

    uuid_int = (
        (timestamp_ms << 80)
        | (0x7 << 76)  # version 7
        | (rand_a << 64)
        | (0x2 << 62)  # variant 10
        | rand_b
    )

    return uuid.UUID(int=uuid_int)


def uuid7_to_str(value: uuid.UUID) -> str:
    """Return the standard string representation of a UUID."""
    return str(value)


def parse_uuid7(value: str) -> uuid.UUID:
    """Parse a UUID string and ensure it is a valid UUID."""
    parsed = uuid.UUID(value)
    return parsed
