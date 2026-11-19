"""Unit tests for the opaque cursor helper (ADR 0002 item 15)."""

from __future__ import annotations

import base64
import json
from datetime import UTC, datetime
from uuid import UUID

import pytest

from lifespace.application.errors import InvalidCursorError
from lifespace.infrastructure.cursor import decode_cursor, encode_cursor
from lifespace.infrastructure.repositories import _decode_keyset, _encode_keyset


def _encode_raw(payload: bytes) -> str:
    """Encode raw bytes as an unpadded base64url string, for malformed-input tests."""
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


@pytest.mark.parametrize(
    "values",
    [
        [],
        ["2026-01-01T00:00:00+00:00", "00000000-0000-0000-0000-000000000001"],
        ["a", "b", "c"],
    ],
)
def test_cursors_round_trip(values: list[str]) -> None:
    """Encoding then decoding returns the same keyset values (ADR 0002 item 15)."""
    cursor = encode_cursor(values)

    assert "=" not in cursor
    assert decode_cursor(cursor, len(values)) == values


@pytest.mark.parametrize(
    ("cursor", "expected_parts"),
    [
        ("", 2),
        ("not base64!", 2),
        (_encode_raw(b"not json"), 2),
        (_encode_raw(json.dumps("just a string").encode()), 2),
        (_encode_raw(json.dumps({"key": "value"}).encode()), 2),
        (_encode_raw(json.dumps(["a", 1]).encode()), 2),
        (encode_cursor(["only-one"]), 2),
        (encode_cursor(["a", "b"]), 3),
    ],
)
def test_malformed_cursors_are_rejected(cursor: str, expected_parts: int) -> None:
    """Anything else raises ``InvalidCursorError`` (ADR 0002 item 15)."""
    with pytest.raises(InvalidCursorError):
        decode_cursor(cursor, expected_parts)


def test_deeply_nested_json_is_rejected() -> None:
    """A deeply nested payload is invalid instead of a RecursionError (ADR 0002 item 24)."""
    cursor = _encode_raw(b"[" * 5000 + b"]" * 5000)

    with pytest.raises(InvalidCursorError):
        decode_cursor(cursor, 2)


def test_non_ascii_cursor_text_is_rejected() -> None:
    """A cursor that is not ASCII is invalid instead of a UnicodeError (ADR 0002 item 24)."""
    with pytest.raises(InvalidCursorError):
        decode_cursor("héllo", 2)


def test_keyset_round_trip() -> None:
    """A normal keyset cursor decodes to its instant and identifier (ADR 0002 item 24)."""
    instant = datetime(2026, 1, 1, 12, tzinfo=UTC)
    item_id = UUID("00000000-0000-0000-0000-000000000001")

    decoded_instant, decoded_id = _decode_keyset(_encode_keyset(instant, item_id))

    assert decoded_instant == instant
    assert decoded_id == item_id


@pytest.mark.parametrize(
    ("instant", "item_id"),
    [
        ("0001-01-01T00:00:00+14:00", "00000000-0000-0000-0000-000000000001"),
        ("9999-12-31T23:59:59-05:00", "00000000-0000-0000-0000-000000000001"),
        ("1969-12-31T23:59:59+00:00", "00000000-0000-0000-0000-000000000001"),
        ("3000-01-01T00:00:00+00:00", "00000000-0000-0000-0000-000000000001"),
        ("2026-01-01T00:00:00", "00000000-0000-0000-0000-000000000001"),
        ("not-an-instant", "00000000-0000-0000-0000-000000000001"),
        ("📝-not-an-instant", "00000000-0000-0000-0000-000000000001"),
        ("2026-01-01T00:00:00+00:00", "not-a-uuid"),
    ],
)
def test_out_of_range_and_malformed_keysets_are_rejected(instant: str, item_id: str) -> None:
    """An out of range, naive, or malformed keyset is invalid_cursor (ADR 0002 item 24)."""
    cursor = encode_cursor([instant, item_id])

    with pytest.raises(InvalidCursorError):
        _decode_keyset(cursor)
