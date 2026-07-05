"""Unit tests for UUIDv7 helpers."""

import uuid

from app.core.ids import new_uuid7, parse_uuid7, uuid7_to_str


def test_new_uuid7_is_version_7() -> None:
    uid = new_uuid7()
    assert isinstance(uid, uuid.UUID)
    assert uid.version == 7


def test_uuid7_to_str_and_parse() -> None:
    uid = new_uuid7()
    text = uuid7_to_str(uid)
    assert len(text) == 36
    assert parse_uuid7(text) == uid
