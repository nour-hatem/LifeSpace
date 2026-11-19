"""Opaque keyset pagination cursors (ADR 0002 item 15).

A cursor carries only the keyset values and is encoded as unpadded base64url
JSON. Decoding rejects anything that is not the expected shape.
"""

from __future__ import annotations

import base64
import binascii
import json
from collections.abc import Sequence

from lifespace.application.errors import InvalidCursorError


def encode_cursor(values: Sequence[str]) -> str:
    """Encode the keyset values as an opaque base64url cursor (ADR 0002 item 15)."""
    payload = json.dumps(list(values), separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def decode_cursor(cursor: str, expected_parts: int) -> list[str]:
    """Decode a cursor and require exactly ``expected_parts`` string values (ADR 0002 item 24).

    Decoding is total: deeply nested JSON, non-ASCII input, invalid base64, and
    any other malformed payload raise ``InvalidCursorError`` rather than a
    lower level exception (ADR 0002 item 24).
    """
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        payload = base64.b64decode(padded.encode("ascii"), altchars=b"-_", validate=True)
        values = json.loads(payload)
    except (ValueError, UnicodeError, binascii.Error, RecursionError, OverflowError) as error:
        raise InvalidCursorError("the cursor is invalid") from error
    if (
        not isinstance(values, list)
        or len(values) != expected_parts
        or not all(isinstance(value, str) for value in values)
    ):
        raise InvalidCursorError("the cursor is invalid")
    return values
