"""Tests for the delete_task use case (ADR 0002 items 4 and 5)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from lifespace.application.errors import NotFoundError, StaleVersionError
from lifespace.application.models import CreateTaskCommand, TaskFilter
from lifespace.application.ports import UnitOfWorkFactory
from lifespace.application.tasks import (
    create_task,
    delete_task,
    get_task,
    list_task_events,
    list_tasks,
    transition_task,
)
from lifespace.domain.task import TaskStatus
from tests.unit.application.fakes import FakeClock, InMemoryStore, SequentialIdGenerator

START = datetime(2026, 2, 1, 12, tzinfo=UTC)


async def _create(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> UUID:
    """Create one planned task and return its id."""
    clock.set(START)
    result = await create_task(uow_factory, clock, ids, CreateTaskCommand(title="Task"))
    return result.view.stored.task.id


async def test_delete_hides_the_task_from_reads(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """A deleted task disappears from get_task and list_tasks (ADR 0002 item 5)."""
    task_id = await _create(uow_factory, clock, ids)

    await delete_task(uow_factory, clock, task_id, 1)

    with pytest.raises(NotFoundError):
        await get_task(uow_factory, clock, task_id)
    page = await list_tasks(uow_factory, clock, TaskFilter(), limit=10)
    assert page.items == ()


async def test_delete_checks_the_version(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """A stale version is rejected and the task stays visible (ADR 0002 item 4)."""
    task_id = await _create(uow_factory, clock, ids)

    with pytest.raises(StaleVersionError) as error:
        await delete_task(uow_factory, clock, task_id, 2)

    assert error.value.expected_version == 2
    assert error.value.current_version == 1
    assert (await get_task(uow_factory, clock, task_id)).stored.version == 1


async def test_deleting_twice_raises_not_found(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """A second delete sees no task and raises NotFoundError (ADR 0002 item 5)."""
    task_id = await _create(uow_factory, clock, ids)
    await delete_task(uow_factory, clock, task_id, 1)

    with pytest.raises(NotFoundError):
        await delete_task(uow_factory, clock, task_id, 2)


async def test_deleting_a_missing_task_raises_not_found(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
) -> None:
    """An unknown id raises NotFoundError (ADR 0002 item 5)."""
    with pytest.raises(NotFoundError):
        await delete_task(uow_factory, clock, UUID(int=99), 1)


async def test_events_stay_stored_after_delete(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    store: InMemoryStore,
) -> None:
    """The append-only events survive a soft delete but are no longer listed (ADR 0002 item 5)."""
    task_id = await _create(uow_factory, clock, ids)
    clock.set(START + timedelta(minutes=1))
    await transition_task(uow_factory, clock, ids, task_id, TaskStatus.IN_PROGRESS, 1)
    clock.set(START + timedelta(minutes=2))

    await delete_task(uow_factory, clock, task_id, 2)

    assert len(store.events[task_id]) == 1
    with pytest.raises(NotFoundError):
        await list_task_events(uow_factory, task_id, limit=10)
