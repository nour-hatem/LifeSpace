"""Tests for the list_tasks use case (ADR 0002 items 15 and 16)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from lifespace.application.errors import InvalidCursorError, ValidationFailedError
from lifespace.application.models import CreateTaskCommand, Page, TaskFilter, TaskView
from lifespace.application.ports import UnitOfWorkFactory
from lifespace.application.tasks import create_task, list_tasks
from lifespace.domain.lifecycle import transition_task
from lifespace.domain.task import Category, Priority, TaskStatus
from tests.unit.application.fakes import FakeClock, SequentialIdGenerator

START = datetime(2026, 3, 1, tzinfo=UTC)


async def _create(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    *,
    title: str,
    status: TaskStatus = TaskStatus.PLANNED,
    category: Category | None = None,
    priority: Priority | None = None,
) -> UUID:
    """Create one task and return its id."""
    result = await create_task(
        uow_factory,
        clock,
        ids,
        CreateTaskCommand(
            title=title,
            status=status,
            category=category,
            priority=priority,
        ),
    )
    return result.view.stored.task.id


async def _seed(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    count: int,
) -> list[UUID]:
    """Create ``count`` tasks one minute apart and return their ids in creation order."""
    created: list[UUID] = []
    for index in range(count):
        clock.set(START + timedelta(minutes=index))
        created.append(await _create(uow_factory, clock, ids, title=f"Task {index}"))
    return created


async def _to_in_progress(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    task_id: UUID,
) -> None:
    """Move a stored task to in progress through the lifecycle (ADR 0001 item 6)."""
    async with uow_factory() as uow:
        stored = await uow.tasks.get(task_id)
        assert stored is not None
        result = transition_task(stored.task, TaskStatus.IN_PROGRESS, now=clock.now())
        await uow.tasks.save(result.task, expected_version=stored.version)
        await uow.commit()


async def test_orders_newest_first(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """Tasks are ordered by created_at descending then id descending (ADR 0002 item 15)."""
    created = await _seed(uow_factory, clock, ids, 3)

    page = await list_tasks(uow_factory, clock, TaskFilter(), limit=10)

    assert [view.stored.task.id for view in page.items] == list(reversed(created))
    assert page.next_cursor is None


async def test_filters_by_several_statuses(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """An empty status set means all, a given set matches those statuses (ADR 0002 item 16)."""
    clock.set(START)
    planned = await _create(uow_factory, clock, ids, title="planned")
    clock.set(START + timedelta(minutes=1))
    await _create(uow_factory, clock, ids, title="inbox", status=TaskStatus.INBOX)
    clock.set(START + timedelta(minutes=2))
    in_progress = await _create(uow_factory, clock, ids, title="in progress")
    await _to_in_progress(uow_factory, clock, in_progress)

    everything = await list_tasks(uow_factory, clock, TaskFilter(), limit=10)
    selected = await list_tasks(
        uow_factory,
        clock,
        TaskFilter(statuses=frozenset({TaskStatus.PLANNED, TaskStatus.IN_PROGRESS})),
        limit=10,
    )

    assert len(everything.items) == 3
    assert [view.stored.task.id for view in selected.items] == [in_progress, planned]


async def test_filters_by_category(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """A category filter keeps only matching tasks (ADR 0002 item 16)."""
    clock.set(START)
    work = await _create(uow_factory, clock, ids, title="work", category=Category.WORK)
    clock.set(START + timedelta(minutes=1))
    await _create(uow_factory, clock, ids, title="personal", category=Category.PERSONAL)
    clock.set(START + timedelta(minutes=2))
    later_work = await _create(uow_factory, clock, ids, title="later work", category=Category.WORK)

    page = await list_tasks(uow_factory, clock, TaskFilter(category=Category.WORK), limit=10)

    assert [view.stored.task.id for view in page.items] == [later_work, work]


async def test_filters_by_priority(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """A priority filter keeps only matching tasks (ADR 0002 item 16)."""
    clock.set(START)
    high = await _create(uow_factory, clock, ids, title="high", priority=Priority.HIGH)
    clock.set(START + timedelta(minutes=1))
    await _create(uow_factory, clock, ids, title="low", priority=Priority.LOW)

    page = await list_tasks(uow_factory, clock, TaskFilter(priority=Priority.HIGH), limit=10)

    assert [view.stored.task.id for view in page.items] == [high]


async def test_paginates_without_gaps_or_duplicates(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """A cursor walk over 5 tasks in pages of 2 gives 3 pages without repeats (ADR 0002 item 15)."""
    created = await _seed(uow_factory, clock, ids, 5)
    expected = list(reversed(created))
    seen: list[UUID] = []
    cursor: str | None = None
    pages = 0

    while True:
        page = await list_tasks(uow_factory, clock, TaskFilter(), limit=2, cursor=cursor)
        pages += 1
        seen.extend(view.stored.task.id for view in page.items)
        if pages < 3:
            assert page.next_cursor is not None
        else:
            assert page.next_cursor is None
        cursor = page.next_cursor
        if cursor is None:
            break

    assert pages == 3
    assert seen == expected


@pytest.mark.parametrize("limit", [0, 201])
async def test_rejects_out_of_range_limits(
    limit: int,
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
) -> None:
    """The page limit must be between 1 and 200 (ADR 0002 item 15)."""
    with pytest.raises(ValidationFailedError) as error:
        await list_tasks(uow_factory, clock, TaskFilter(), limit=limit)

    assert error.value.field == "limit"


async def test_a_malformed_cursor_is_rejected(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """An undecodable cursor is an invalid cursor (ADR 0002 item 15)."""
    await _seed(uow_factory, clock, ids, 3)

    with pytest.raises(InvalidCursorError):
        await list_tasks(uow_factory, clock, TaskFilter(), limit=2, cursor="garbage")


async def test_empty_store_returns_an_empty_page(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
) -> None:
    """An empty store returns an empty page without a cursor (ADR 0002 item 15)."""
    page: Page[TaskView] = await list_tasks(uow_factory, clock, TaskFilter(), limit=10)

    assert page.items == ()
    assert page.next_cursor is None
