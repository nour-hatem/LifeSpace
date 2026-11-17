"""Fixtures shared by the application use case tests."""

from __future__ import annotations

import pytest

from lifespace.application.ports import UnitOfWorkFactory
from tests.unit.application.fakes import (
    FakeClock,
    InMemoryStore,
    InMemoryUnitOfWork,
    SequentialIdGenerator,
)


def _factory(store: InMemoryStore) -> UnitOfWorkFactory:
    """Return a factory that opens a transaction over ``store``."""

    def create() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(store)

    return create


@pytest.fixture
def store() -> InMemoryStore:
    """Return an empty shared store."""
    return InMemoryStore()


@pytest.fixture
def clock() -> FakeClock:
    """Return a clock fixed at 2026-01-01T00:00:00Z."""
    return FakeClock()


@pytest.fixture
def ids() -> SequentialIdGenerator:
    """Return a generator that yields UUID(int=1), UUID(int=2), and so on."""
    return SequentialIdGenerator()


@pytest.fixture
def uow_factory(store: InMemoryStore) -> UnitOfWorkFactory:
    """Return a factory that opens a transaction over ``store``."""
    return _factory(store)
