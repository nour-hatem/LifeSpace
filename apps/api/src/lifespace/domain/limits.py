"""Input bounds shared by domain objects (ADR 0002 item 20).

The constants and helpers here keep values inside the ranges PostgreSQL can
store, so an out of range value is a domain validation failure instead of a
database error or a 500 (ADR 0002 items 20, 21, and 24).
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from lifespace.domain.errors import DomainValidationError

MIN_INSTANT = datetime(1970, 1, 1, tzinfo=UTC)
MAX_INSTANT = datetime(3000, 1, 1, tzinfo=UTC)
MIN_DATE = date(1970, 1, 1)
MAX_DATE = date(2999, 12, 31)
MAX_TITLE_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 20_000
MAX_REASON_LENGTH = 1_000
MAX_INT32 = 2_147_483_647


def ensure_text(value: str, *, field: str, max_length: int) -> str:
    """Return ``value`` when PostgreSQL can store it (ADR 0002 item 20).

    Raises ``DomainValidationError`` when the text is longer than
    ``max_length``, contains the NUL character, or contains a surrogate code
    point. Non-Latin text and emoji are accepted.
    """
    if len(value) > max_length:
        raise DomainValidationError(
            f"{field} must be at most {max_length} characters",
            field=field,
        )
    if "\x00" in value:
        raise DomainValidationError(f"{field} must not contain the NUL character", field=field)
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise DomainValidationError(
            f"{field} must not contain a surrogate code point",
            field=field,
        )
    return value


def ensure_date_in_range(value: date, *, field: str) -> date:
    """Return ``value`` when it lies in the supported date range (ADR 0002 item 20).

    The supported range is ``MIN_DATE <= value <= MAX_DATE``.
    """
    if not MIN_DATE <= value <= MAX_DATE:
        raise DomainValidationError(
            f"{field} must be between {MIN_DATE.isoformat()} and {MAX_DATE.isoformat()}",
            field=field,
        )
    return value
