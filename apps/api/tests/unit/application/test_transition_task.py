"""Tests for the transition_task use case (ADR 0001 items 6 to 9, ADR 0002 item 6)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID

import pytest

from lifespace.application.errors import (
    NotFoundError,
    StaleVersionError,
    TransitionRejectedError,
)
from lifespace.application.models import CreateTaskCommand
from lifespace.application.ports import UnitOfWorkFactory
from lifespace.application.tasks import create_task, get_task, transition_task
from lifespace.domain.deadline import DateDeadline
from lifespace.domain.lifecycle import StatusEvent
from lifespace.domain.task import TaskStatus
from lifespace.domain.time import TimeInterval
from tests.unit.application.fakes import (
    FakeClock,
    InMemoryStore,
    InMemoryTaskRepository,
    InMemoryUnitOfWork,
    SequentialIdGenerator,
)

START = datetime(2026, 2, 1, 12, tzinfo=UTC)


class _FailingEventRepository(InMemoryTaskRepository):
    """A task repository whose event append always fails (ADR 0002 item 6)."""

    async def add_event(self, event_id: UUID, event: StatusEvent) -> None:
        """Fail instead of appending the event."""
        raise RuntimeError("event write failed")


class _FailingEventUnitOfWork(InMemoryUnitOfWork):
    """A unit of work that uses the failing event repository (ADR 0002 item 6)."""

    async def __aenter__(self) -> _FailingEventUnitOfWork:
        """Open the transaction and swap in the failing repository."""
        await super().__aenter__()
        working = self._working
        assert working is not None
        self.tasks = _FailingEventRepository(working)
        return self


def _failing_factory(store: InMemoryStore) -> UnitOfWorkFactory:
    """Return a factory whose event writes fail (ADR 0002 item 6)."""

    def create() -> InMemoryUnitOfWork:
        return _FailingEventUnitOfWork(store)

    return create


async def _create(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    status: TaskStatus = TaskStatus.PLANNED,
) -> UUID:
    """Create one task with ``status`` and return its id."""
    clock.set(START)
    result = await create_task(
        uow_factory,
        clock,
        ids,
        CreateTaskCommand(title="Task", status=status),
    )
    return result.view.stored.task.id


@pytest.mark.parametrize(
    ("from_status", "to_status"),
    [
        (TaskStatus.PLANNED, TaskStatus.IN_PROGRESS),
        (TaskStatus.PLANNED, TaskStatus.COMPLETED),
        (TaskStatus.PLANNED, TaskStatus.CANCELED),
        (TaskStatus.INBOX, TaskStatus.PLANNED),
        (TaskStatus.INBOX, TaskStatus.IN_PROGRESS),
        (TaskStatus.INBOX, TaskStatus.CANCELED),
    ],
)
async def test_allowed_first_transitions_store_one_event(
    from_status: TaskStatus,
    to_status: TaskStatus,
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    store: InMemoryStore,
) -> None:
    """Every allowed first transition bumps the version and appends one event (ADR 0002 item 6)."""
    task_id = await _create(uow_factory, clock, ids, from_status)
    clock.set(START + timedelta(minutes=1))

    view = await transition_task(uow_factory, clock, ids, task_id, to_status, 1)

    assert view.stored.task.status is to_status
    assert view.stored.version == 2
    events = store.events[task_id]
    assert len(events) == 1
    assert events[0].id == UUID(int=2)
    event = events[0].event
    assert event.from_status is from_status
    assert event.to_status is to_status
    assert event.occurred_at == clock.now()


async def test_cancel_stores_the_stripped_reason(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    store: InMemoryStore,
) -> None:
    """Canceling records the stripped reason on the task and the event (ADR 0001 item 7)."""
    task_id = await _create(uow_factory, clock, ids)
    clock.set(START + timedelta(minutes=1))

    view = await transition_task(
        uow_factory,
        clock,
        ids,
        task_id,
        TaskStatus.CANCELED,
        1,
        reason="  no longer needed  ",
    )

    assert view.stored.task.status is TaskStatus.CANCELED
    assert view.stored.task.canceled_at == clock.now()
    assert view.stored.task.cancellation_reason == "no longer needed"
    assert store.events[task_id][0].event.reason == "no longer needed"


async def test_reopen_after_complete_restores_planned(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    store: InMemoryStore,
) -> None:
    """Reopening clears the lifecycle timestamps and adds a second event (ADR 0001 item 8)."""
    task_id = await _create(uow_factory, clock, ids)
    clock.set(START + timedelta(minutes=1))
    await transition_task(uow_factory, clock, ids, task_id, TaskStatus.COMPLETED, 1)
    clock.set(START + timedelta(minutes=2))

    view = await transition_task(uow_factory, clock, ids, task_id, TaskStatus.PLANNED, 2)

    assert view.stored.task.status is TaskStatus.PLANNED
    assert view.stored.task.completed_at is None
    assert view.stored.version == 3
    assert len(store.events[task_id]) == 2


async def test_reopen_discards_an_ended_schedule(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    store: InMemoryStore,
) -> None:
    """A schedule that ended is dropped and recorded on the reopen event (ADR 0001 item 8)."""
    schedule = TimeInterval(
        start=START + timedelta(minutes=30),
        end=START + timedelta(minutes=90),
    )
    clock.set(START)
    created = await create_task(
        uow_factory,
        clock,
        ids,
        CreateTaskCommand(title="Task", scheduled=schedule),
    )
    task_id = created.view.stored.task.id
    clock.set(START + timedelta(minutes=5))
    await transition_task(uow_factory, clock, ids, task_id, TaskStatus.COMPLETED, 1)
    clock.set(START + timedelta(hours=3))

    view = await transition_task(uow_factory, clock, ids, task_id, TaskStatus.PLANNED, 2)

    assert view.stored.task.scheduled is None
    assert store.events[task_id][1].event.discarded_schedule == schedule


async def test_inbox_to_completed_is_rejected_and_writes_nothing(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    store: InMemoryStore,
) -> None:
    """An illegal transition explains the allowed next statuses (ADR 0001 item 6)."""
    task_id = await _create(uow_factory, clock, ids, TaskStatus.INBOX)

    with pytest.raises(TransitionRejectedError) as error:
        await transition_task(uow_factory, clock, ids, task_id, TaskStatus.COMPLETED, 1)

    assert "allowed next statuses" in error.value.message
    assert "planned" in error.value.message
    assert store.tasks[task_id].version == 1
    assert store.tasks[task_id].task.status is TaskStatus.INBOX
    assert store.events == {}


async def test_completed_to_completed_is_rejected_and_writes_nothing(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    store: InMemoryStore,
) -> None:
    """A transition to the same status is rejected and adds no event (ADR 0001 item 6)."""
    task_id = await _create(uow_factory, clock, ids)
    clock.set(START + timedelta(minutes=1))
    await transition_task(uow_factory, clock, ids, task_id, TaskStatus.COMPLETED, 1)

    with pytest.raises(TransitionRejectedError) as error:
        await transition_task(uow_factory, clock, ids, task_id, TaskStatus.COMPLETED, 2)

    assert "allowed next statuses: planned" in error.value.message
    assert store.tasks[task_id].version == 2
    assert store.tasks[task_id].task.status is TaskStatus.COMPLETED
    assert len(store.events[task_id]) == 1


async def test_stale_version_is_rejected_and_writes_nothing(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    store: InMemoryStore,
) -> None:
    """A stale version is checked before the domain rule and writes nothing (ADR 0002 item 4)."""
    task_id = await _create(uow_factory, clock, ids)
    clock.set(START + timedelta(minutes=1))

    with pytest.raises(StaleVersionError) as error:
        await transition_task(uow_factory, clock, ids, task_id, TaskStatus.IN_PROGRESS, 6)

    assert error.value.expected_version == 6
    assert error.value.current_version == 1
    assert store.tasks[task_id].version == 1
    assert store.events == {}


async def test_missing_task_is_not_found(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """An unknown task raises NotFoundError (ADR 0002 item 5)."""
    with pytest.raises(NotFoundError):
        await transition_task(
            uow_factory,
            clock,
            ids,
            UUID(int=99),
            TaskStatus.IN_PROGRESS,
            1,
        )


async def test_a_completed_task_is_no_longer_overdue(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """Completing a past-due task removes the computed overdue flag (ADR 0001 item 9)."""
    clock.set(START)
    created = await create_task(
        uow_factory,
        clock,
        ids,
        CreateTaskCommand(
            title="Task",
            deadline=DateDeadline(day=date(2026, 1, 1)),
        ),
    )
    task_id = created.view.stored.task.id
    before = await get_task(uow_factory, clock, task_id)
    clock.set(START + timedelta(minutes=1))

    view = await transition_task(uow_factory, clock, ids, task_id, TaskStatus.COMPLETED, 1)

    assert before.is_overdue is True
    assert view.is_overdue is False


async def test_task_and_event_are_committed_together(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    store: InMemoryStore,
) -> None:
    """A failed event append rolls back the task change (ADR 0002 items 2 and 6)."""
    task_id = await _create(uow_factory, clock, ids)
    clock.set(START + timedelta(minutes=1))

    with pytest.raises(RuntimeError):
        await transition_task(
            _failing_factory(store),
            clock,
            ids,
            task_id,
            TaskStatus.IN_PROGRESS,
            1,
        )

    assert store.tasks[task_id].version == 1
    assert store.tasks[task_id].task.status is TaskStatus.PLANNED
    assert store.events == {}
