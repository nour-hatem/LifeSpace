"""Tests for the typed domain errors (ADR 0001 items 6 and 17)."""

from __future__ import annotations

from lifespace.domain.errors import DomainError, DomainValidationError, InvalidTransitionError


def test_domain_error_carries_a_code_and_a_message() -> None:
    error = DomainError("boom")
    assert error.code == "domain_error"
    assert error.message == "boom"
    assert str(error) == "boom"


def test_domain_validation_error_defaults_to_no_field() -> None:
    error = DomainValidationError("bad value")
    assert error.code == "validation_failed"
    assert error.field is None
    assert error.message == "bad value"


def test_domain_validation_error_records_the_field() -> None:
    error = DomainValidationError("bad value", field="title")
    assert error.code == "validation_failed"
    assert error.field == "title"


def test_invalid_transition_error_records_both_statuses() -> None:
    error = InvalidTransitionError("Inbox", "Completed")
    assert error.code == "invalid_transition"
    assert error.from_status == "Inbox"
    assert error.to_status == "Completed"


def test_typed_errors_are_domain_errors() -> None:
    assert issubclass(DomainValidationError, DomainError)
    assert issubclass(InvalidTransitionError, DomainError)
