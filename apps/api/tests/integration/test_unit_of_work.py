"""Integration tests for the transactional unit of work (ADR 0002 item 2)."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID, uuid7

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from lifespace.application.ports import UnitOfWorkFactory
from lifespace.domain.task import Task, create_task, edit_task
from lifespace.infrastructure.db import create_engine, create_session_factory
from lifespace.infrastructure.unit_of_work import (
    SqlAlchemyUnitOfWork,
    create_unit_of_work_factory,
)
from tests.integration.conftest import require_test_database_url_sync, reset_database, run_alembic

NOW = datetime(2026, 1, 1, 12, tzinfo=UTC)


@pytest.fixture(scope="module")
def database_url() -> str:
    """Upgrade the test database to head for repository tests (ADR 0002 item 19)."""
    url = require_test_database_url_sync()
    result = run_alembic(url, "upgrade", "head")
    assert result.returncode == 0, result.stderr
    return url


@pytest.fixture
async def engine(database_url: str) -> AsyncIterator[AsyncEngine]:
    """Open one engine for a test and dispose it afterwards (ADR 0002 item 2)."""
    engine = create_engine(database_url)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Return a session factory over the test engine (ADR 0002 item 2)."""
    return create_session_factory(engine)


@pytest.fixture(autouse=True)
def empty_database(database_url: str) -> Iterator[None]:
    """Start and end every test from an empty M2 schema."""
    reset_database(database_url)
    yield
    reset_database(database_url)


@pytest.fixture
def factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> UnitOfWorkFactory:
    """Return a real unit of work factory over the test database."""
    return create_unit_of_work_factory(session_factory)


def _new_task(title: str = "Task", task_id: UUID | None = None) -> Task:
    """Build a valid planned task for the unit of work tests."""
    return create_task(
        task_id=task_id if task_id is not None else uuid7(),
        title=title,
        now=NOW,
    )


async def test_commit_persists_every_change(factory: UnitOfWorkFactory) -> None:
    """A committed unit of work is visible to the next one (ADR 0002 item 2)."""
    task = _new_task()

    async with factory() as uow:
        await uow.tasks.add(task)
        await uow.commit()

    async with factory() as uow:
        stored = await uow.tasks.get(task.id)
    assert stored is not None
    assert stored.version == 1


async def test_leaving_without_commit_rolls_back(factory: UnitOfWorkFactory) -> None:
    """Leaving the block without a commit discards the writes (ADR 0002 item 2)."""
    task = _new_task()

    async with factory() as uow:
        await uow.tasks.add(task)

    async with factory() as uow:
        assert await uow.tasks.get(task.id) is None


async def test_an_exception_inside_the_block_rolls_back(factory: UnitOfWorkFactory) -> None:
    """An exception discards the writes even when none were committed (ADR 0002 item 2)."""
    task = _new_task()

    with pytest.raises(RuntimeError):
        async with factory() as uow:
            await uow.tasks.add(task)
            raise RuntimeError("boom")

    async with factory() as uow:
        assert await uow.tasks.get(task.id) is None


async def test_explicit_rollback_discards_the_writes(factory: UnitOfWorkFactory) -> None:
    """``rollback`` discards pending writes while the block is still open (ADR 0002 item 2)."""
    task = _new_task()

    async with factory() as uow:
        await uow.tasks.add(task)
        await uow.rollback()

    async with factory() as uow:
        assert await uow.tasks.get(task.id) is None


async def test_two_units_do_not_see_uncommitted_rows(factory: UnitOfWorkFactory) -> None:
    """Isolation holds until the writer commits (ADR 0002 item 2)."""
    task = _new_task()

    async with factory() as first:
        await first.tasks.add(task)
        async with factory() as second:
            assert await second.tasks.get(task.id) is None
        await first.commit()

    async with factory() as third:
        assert await third.tasks.get(task.id) is not None


async def test_the_session_is_closed_afterwards(factory: UnitOfWorkFactory) -> None:
    """The session is closed whether the block commits or not (ADR 0002 item 2)."""
    task = _new_task()

    uow = factory()
    async with uow:
        session = cast(SqlAlchemyUnitOfWork, uow)._session
        assert session is not None
        await uow.tasks.add(task)
        await uow.commit()

    assert cast(SqlAlchemyUnitOfWork, uow)._session is None
    assert session.in_transaction() is False


async def test_a_unit_of_work_is_single_use(factory: UnitOfWorkFactory) -> None:
    """A unit of work instance cannot be entered twice (ADR 0002 item 2)."""
    uow = factory()

    async with uow:
        pass

    with pytest.raises(RuntimeError):
        async with uow:
            pass


async def test_a_failure_after_save_rolls_back_the_task_change(
    factory: UnitOfWorkFactory,
) -> None:
    """A failure between saving a task and adding its event leaves neither (ADR 0002 item 6)."""
    task = _new_task(title="Original")
    async with factory() as uow:
        await uow.tasks.add(task)
        await uow.commit()

    with pytest.raises(RuntimeError):
        async with factory() as uow:
            stored = await uow.tasks.get(task.id)
            assert stored is not None
            edited = edit_task(
                stored.task,
                now=NOW + timedelta(minutes=1),
                title="Changed",
            )
            await uow.tasks.save(edited, expected_version=1)
            raise RuntimeError("event write failed")

    async with factory() as uow:
        stored = await uow.tasks.get(task.id)
        events = await uow.tasks.list_events(task.id, limit=10)

    assert stored is not None
    assert stored.version == 1
    assert stored.task.title == "Original"
    assert events.items == ()
