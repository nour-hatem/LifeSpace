"""Tests for the list_task_events use case (ADR 0002 items 5, 6, and 15)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from lifespace.application.errors import NotFoundError, ValidationFailedError
from lifespace.application.models import CreateTaskCommand
from lifespace.application.ports import UnitOfWorkFactory
from lifespace.application.tasks import (
    create_task,
    delete_task,
    list_task_events,
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


async def test_events_are_newest_first(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """Events are ordered by occurred_at descending then id descending (ADR 0002 item 15)."""
    task_id = await _create(uow_factory, clock, ids)
    clock.set(START + timedelta(minutes=1))
    await transition_task(uow_factory, clock, ids, task_id, TaskStatus.IN_PROGRESS, 1)
    clock.set(START + timedelta(minutes=2))
    await transition_task(uow_factory, clock, ids, task_id, TaskStatus.COMPLETED, 2)

    page = await list_task_events(uow_factory, task_id, limit=10)

    assert [stored.event.to_status for stored in page.items] == [
        TaskStatus.COMPLETED,
        TaskStatus.IN_PROGRESS,
    ]
    assert page.next_cursor is None


async def test_paginates_without_duplicates(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """A cursor walk over five events in pages of two yields three pages (ADR 0002 item 15)."""
    task_id = await _create(uow_factory, clock, ids)
    expected_version = 1
    for index, to_status in enumerate(
        [
            TaskStatus.IN_PROGRESS,
            TaskStatus.COMPLETED,
            TaskStatus.PLANNED,
            TaskStatus.IN_PROGRESS,
            TaskStatus.COMPLETED,
        ]
    ):
        clock.set(START + timedelta(minutes=index + 1))
        await transition_task(
            uow_factory,
            clock,
            ids,
            task_id,
            to_status,
            expected_version,
        )
        expected_version += 1

    seen: list[UUID] = []
    cursor: str | None = None
    pages = 0
    while True:
        page = await list_task_events(uow_factory, task_id, limit=2, cursor=cursor)
        pages += 1
        seen.extend(stored.id for stored in page.items)
        if pages < 3:
            assert page.next_cursor is not None
        else:
            assert page.next_cursor is None
        cursor = page.next_cursor
        if cursor is None:
            break

    assert pages == 3
    assert len(seen) == 5
    assert len(set(seen)) == 5


@pytest.mark.parametrize("limit", [0, 201])
async def test_rejects_out_of_range_limits(
    limit: int,
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """The page limit must be between 1 and 200 (ADR 0002 item 15)."""
    task_id = await _create(uow_factory, clock, ids)

    with pytest.raises(ValidationFailedError) as error:
        await list_task_events(uow_factory, task_id, limit=limit)

    assert error.value.field == "limit"


async def test_missing_task_is_not_found(
    uow_factory: UnitOfWorkFactory,
) -> None:
    """An unknown task raises NotFoundError (ADR 0002 item 5)."""
    with pytest.raises(NotFoundError):
        await list_task_events(uow_factory, UUID(int=99), limit=10)


async def test_deleted_task_is_not_found(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    store: InMemoryStore,
) -> None:
    """A deleted task keeps its events but no longer lists them (ADR 0002 items 5 and 6)."""
    task_id = await _create(uow_factory, clock, ids)
    clock.set(START + timedelta(minutes=1))
    await transition_task(uow_factory, clock, ids, task_id, TaskStatus.IN_PROGRESS, 1)
    clock.set(START + timedelta(minutes=2))
    await delete_task(uow_factory, clock, task_id, 2)

    assert len(store.events[task_id]) == 1
    with pytest.raises(NotFoundError):
        await list_task_events(uow_factory, task_id, limit=10)
