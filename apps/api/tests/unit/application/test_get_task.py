"""Tests for the get_task use case (ADR 0002 items 5 and 8)."""

from __future__ import annotations

from uuid import UUID

import pytest

from lifespace.application.errors import NotFoundError
from lifespace.application.models import CreateTaskCommand
from lifespace.application.ports import UnitOfWorkFactory
from lifespace.application.tasks import create_task, get_task
from tests.unit.application.fakes import FakeClock, SequentialIdGenerator


async def test_returns_the_stored_task(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """A stored task is returned with its version and overdue flag (ADR 0002 items 3, 4, and 8)."""
    created = await create_task(uow_factory, clock, ids, CreateTaskCommand(title="Write report"))

    view = await get_task(uow_factory, clock, created.view.stored.task.id)

    assert view.stored.task.id == created.view.stored.task.id
    assert view.stored.version == 1
    assert view.is_overdue is False


async def test_missing_task_raises_not_found(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
) -> None:
    """An unknown id is a NotFoundError (ADR 0002 item 5)."""
    with pytest.raises(NotFoundError):
        await get_task(uow_factory, clock, UUID(int=99))


async def test_soft_deleted_task_raises_not_found(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """A soft deleted task is invisible to reads (ADR 0002 item 5)."""
    created = await create_task(uow_factory, clock, ids, CreateTaskCommand(title="Write report"))
    task_id = created.view.stored.task.id

    async with uow_factory() as uow:
        await uow.tasks.soft_delete(task_id, expected_version=1, now=clock.now())
        await uow.commit()

    with pytest.raises(NotFoundError):
        await get_task(uow_factory, clock, task_id)
