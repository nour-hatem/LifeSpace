"""Tests for the computed overdue flag in task views (ADR 0002 item 8)."""

from __future__ import annotations

from datetime import UTC, date, datetime

from lifespace.application.models import CreateTaskCommand, TaskFilter
from lifespace.application.ports import UnitOfWorkFactory
from lifespace.application.settings import update_timezone
from lifespace.application.tasks import create_task, get_task, list_tasks
from lifespace.domain.deadline import DateDeadline
from tests.unit.application.fakes import FakeClock, SequentialIdGenerator

BOUNDARY = datetime(2026, 4, 23, 22, 0, tzinfo=UTC)


async def test_date_deadline_flips_at_the_verified_instant(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """The Cairo deadline day 2026-04-23 ends at 2026-04-23T22:00:00Z (ADR 0001 item 2)."""
    clock.set(datetime(2026, 4, 1, 12, tzinfo=UTC))
    await update_timezone(uow_factory, clock, "Africa/Cairo")
    created = await create_task(
        uow_factory,
        clock,
        ids,
        CreateTaskCommand(title="File taxes", deadline=DateDeadline(day=date(2026, 4, 23))),
    )
    task_id = created.view.stored.task.id

    clock.set(datetime(2026, 4, 23, 21, 59, 59, tzinfo=UTC))
    before = await get_task(uow_factory, clock, task_id)

    clock.set(BOUNDARY)
    at_boundary = await get_task(uow_factory, clock, task_id)
    page = await list_tasks(uow_factory, clock, TaskFilter(), limit=10)

    assert before.is_overdue is False
    assert at_boundary.is_overdue is True
    assert page.items[0].is_overdue is True


async def test_the_same_task_is_judged_differently_in_another_zone(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """Overdue depends on the stored zone, not on the task (ADR 0002 item 8)."""
    clock.set(datetime(2026, 4, 1, 12, tzinfo=UTC))
    created = await create_task(
        uow_factory,
        clock,
        ids,
        CreateTaskCommand(title="File taxes", deadline=DateDeadline(day=date(2026, 4, 23))),
    )
    task_id = created.view.stored.task.id
    clock.set(BOUNDARY)

    await update_timezone(uow_factory, clock, "UTC")
    under_utc = await get_task(uow_factory, clock, task_id)

    await update_timezone(uow_factory, clock, "Africa/Cairo")
    under_cairo = await get_task(uow_factory, clock, task_id)

    assert under_utc.is_overdue is False
    assert under_cairo.is_overdue is True


async def test_a_task_without_a_deadline_is_never_overdue(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """Overdue requires a deadline (ADR 0001 item 9)."""
    clock.set(datetime(2026, 4, 1, 12, tzinfo=UTC))
    created = await create_task(uow_factory, clock, ids, CreateTaskCommand(title="No deadline"))

    clock.set(datetime(2030, 1, 1, tzinfo=UTC))
    view = await get_task(uow_factory, clock, created.view.stored.task.id)

    assert view.is_overdue is False
