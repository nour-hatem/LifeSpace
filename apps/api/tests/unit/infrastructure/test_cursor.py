"""Unit tests for the opaque cursor helper (ADR 0002 item 15)."""

from __future__ import annotations

import base64
import json

import pytest

from lifespace.application.errors import InvalidCursorError
from lifespace.infrastructure.cursor import decode_cursor, encode_cursor


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
