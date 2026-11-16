"""Typed errors raised by the domain layer (ADR 0001 item 17)."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for every domain error, carrying a stable ``code`` and a message.

    The API layer maps these errors to problem+json responses in M2 (ADR 0001
    item 17).
    """

    code: str = "domain_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class DomainValidationError(DomainError):
    """A domain rule rejected a value (ADR 0001 item 17).

    ``field`` names the rejected input when it is known, so callers can build
    field level detail.
    """

    code: str = "validation_failed"

    def __init__(self, message: str, *, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field


class InvalidTransitionError(DomainError):
    """A lifecycle transition is not allowed (ADR 0001 item 17).

    Used by the task lifecycle in Part 3; it records both statuses so the
    rejection can explain the allowed next statuses (ADR 0001 item 6).
    """

    code: str = "invalid_transition"

    def __init__(self, from_status: str, to_status: str) -> None:
        super().__init__(f"transition from {from_status!r} to {to_status!r} is not allowed")
        self.from_status = from_status
        self.to_status = to_status
