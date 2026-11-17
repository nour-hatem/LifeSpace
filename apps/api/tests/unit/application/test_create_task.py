"""Tests for the create_task use case (ADR 0002 items 3, 4, and 9)."""

from __future__ import annotations

from uuid import UUID

import pytest

from lifespace.application.errors import ValidationFailedError
from lifespace.application.models import CreateTaskCommand
from lifespace.application.ports import UnitOfWorkFactory
from lifespace.application.tasks import create_task
from lifespace.domain.task import TaskSource, TaskStatus
from tests.unit.application.fakes import FakeClock, InMemoryStore, SequentialIdGenerator


async def test_creates_a_planned_manual_task_at_the_clock_instant(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """Creation defaults to PLANNED, MANUAL, and version 1 (ADR 0002 items 3, 4, and 9)."""
    result = await create_task(uow_factory, clock, ids, CreateTaskCommand(title="Write report"))

    task = result.view.stored.task
    assert result.replayed is False
    assert result.view.stored.version == 1
    assert task.status is TaskStatus.PLANNED
    assert task.source is TaskSource.MANUAL
    assert task.title == "Write report"
    assert task.id == UUID(int=1)
    assert task.created_at == clock.now()
    assert task.updated_at == clock.now()


async def test_accepts_inbox_status(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """An unreviewed capture may start in the inbox (ADR 0001 item 4)."""
    result = await create_task(
        uow_factory,
        clock,
        ids,
        CreateTaskCommand(title="Call the bank", status=TaskStatus.INBOX),
    )

    assert result.view.stored.task.status is TaskStatus.INBOX


@pytest.mark.parametrize(
    "status",
    [TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED, TaskStatus.CANCELED],
)
async def test_rejects_other_creation_statuses(
    status: TaskStatus,
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """Only INBOX and PLANNED can be created (ADR 0001 item 4)."""
    with pytest.raises(ValidationFailedError) as error:
        await create_task(
            uow_factory,
            clock,
            ids,
            CreateTaskCommand(title="Task", status=status),
        )

    assert error.value.field == "status"


async def test_rejects_an_empty_title(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """A blank title is a validation failure with a field (ADR 0001 item 11)."""
    with pytest.raises(ValidationFailedError) as error:
        await create_task(uow_factory, clock, ids, CreateTaskCommand(title="   "))

    assert error.value.field == "title"


async def test_a_failed_creation_stores_nothing(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    store: InMemoryStore,
) -> None:
    """The unit of work leaves without commit and discards its copy (ADR 0002 item 2)."""
    with pytest.raises(ValidationFailedError):
        await create_task(uow_factory, clock, ids, CreateTaskCommand(title=""))

    assert store.tasks == {}
