"""Typed application errors and domain error translation (ADR 0002 items 4, 12 to 15)."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from lifespace.domain.errors import DomainValidationError, InvalidTransitionError


class ApplicationError(Exception):
    """Base class for every application error (ADR 0002 items 12 and 13).

    ``code`` is the stable machine readable identifier, ``result`` is the result
    category the API layer maps to a problem+json response, and ``message``
    explains the failure without internal details.
    """

    code: str = "failed"
    result: str = "failed"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(ApplicationError):
    """A requested record does not exist or is soft deleted (ADR 0002 item 5)."""

    code = "not_found"
    result = "not_found"

    def __init__(self, message: str = "the requested record was not found") -> None:
        super().__init__(message)


class StaleVersionError(ApplicationError):
    """An update carried an expected version that is no longer current (ADR 0002 item 4)."""

    code = "stale_version"
    result = "conflict"

    def __init__(self, expected_version: int, current_version: int | None) -> None:
        message = f"expected version {expected_version} is stale"
        if current_version is not None:
            message = f"{message}; the current version is {current_version}"
        super().__init__(message)
        self.expected_version = expected_version
        self.current_version = current_version


class ValidationFailedError(ApplicationError):
    """An input failed application validation (ADR 0002 items 12 and 17)."""

    code = "validation_failed"
    result = "validation_failed"

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field


class TransitionRejectedError(ApplicationError):
    """A lifecycle transition was rejected by the domain (ADR 0002 items 12 and 13)."""

    code = "invalid_transition"
    result = "rejected"

    def __init__(self, message: str, from_status: str, to_status: str) -> None:
        super().__init__(message)
        self.from_status = from_status
        self.to_status = to_status


class IdempotencyKeyReuseError(ApplicationError):
    """An idempotency key was reused for another request or a deleted task (ADR 0002 item 14)."""

    code = "idempotency_key_reuse"
    result = "rejected"

    def __init__(self, message: str = "the idempotency key was already used") -> None:
        super().__init__(message)


class IdempotencyInProgressError(ApplicationError):
    """Another request is already recording this idempotency key (ADR 0002 item 14)."""

    code = "idempotency_in_progress"
    result = "conflict"

    def __init__(self, message: str = "the idempotency key is already in progress") -> None:
        super().__init__(message)


class InvalidCursorError(ApplicationError):
    """A pagination cursor cannot be decoded (ADR 0002 item 15)."""

    code = "invalid_cursor"
    result = "validation_failed"

    def __init__(self, message: str = "the cursor is invalid") -> None:
        super().__init__(message)


@contextmanager
def translate_domain_errors() -> Iterator[None]:
    """Translate domain errors into application errors (ADR 0002 items 12 and 17).

    ``DomainValidationError`` keeps its ``field`` and becomes
    ``ValidationFailedError`` (ADR 0002 item 17). ``InvalidTransitionError``
    keeps both statuses and becomes ``TransitionRejectedError`` (ADR 0002 item
    13). The original error is chained so the cause is never lost.
    """
    try:
        yield
    except DomainValidationError as error:
        raise ValidationFailedError(error.message, field=error.field) from error
    except InvalidTransitionError as error:
        raise TransitionRejectedError(
            error.message,
            from_status=error.from_status,
            to_status=error.to_status,
        ) from error
