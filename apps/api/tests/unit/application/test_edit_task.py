"""Tests for the edit_task use case (ADR 0001 items 12 and 16, ADR 0002 item 4)."""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

import pytest
from hypothesis import given
from hypothesis import strategies as st

from lifespace.application.errors import (
    NotFoundError,
    StaleVersionError,
    ValidationFailedError,
)
from lifespace.application.models import CreateTaskCommand, TaskChanges
from lifespace.application.ports import UnitOfWorkFactory
from lifespace.application.tasks import create_task, delete_task, edit_task
from lifespace.domain.deadline import DateDeadline
from lifespace.domain.task import Category, Priority, Task
from lifespace.domain.time import TimeInterval
from tests.unit.application.fakes import (
    FakeClock,
    InMemoryStore,
    InMemoryUnitOfWork,
    SequentialIdGenerator,
)

START = datetime(2026, 2, 1, 12, tzinfo=UTC)

OLD_DEADLINE = DateDeadline(day=date(2026, 5, 1))
NEW_DEADLINE = DateDeadline(day=date(2026, 6, 1))
OLD_SCHEDULE = TimeInterval(
    start=datetime(2026, 4, 1, 9, tzinfo=UTC),
    end=datetime(2026, 4, 1, 10, tzinfo=UTC),
)
NEW_SCHEDULE = TimeInterval(
    start=datetime(2026, 4, 2, 9, tzinfo=UTC),
    end=datetime(2026, 4, 2, 11, tzinfo=UTC),
)

_NEW_DEADLINE = st.one_of(
    st.none(),
    st.builds(
        DateDeadline,
        day=st.dates(min_value=date(2026, 1, 1), max_value=date(2027, 12, 31)),
    ),
)
_NEW_SCHEDULE = st.one_of(
    st.none(),
    st.tuples(
        st.datetimes(
            min_value=datetime(2026, 1, 1),
            max_value=datetime(2027, 1, 1),
            timezones=st.just(UTC),
        ),
        st.integers(min_value=1, max_value=600),
    ).map(lambda pair: TimeInterval(start=pair[0], end=pair[0] + timedelta(minutes=pair[1]))),
)
_NEW_ESTIMATE = st.one_of(st.none(), st.integers(min_value=1, max_value=100_000))


async def _create_full_task(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> Task:
    """Create a task with every optional field set and advance the clock one minute."""
    clock.set(START)
    result = await create_task(
        uow_factory,
        clock,
        ids,
        CreateTaskCommand(
            title="Old title",
            description="old description",
            category=Category.WORK,
            priority=Priority.LOW,
            estimate_minutes=30,
            deadline=OLD_DEADLINE,
            scheduled=OLD_SCHEDULE,
        ),
    )
    clock.set(START + timedelta(minutes=1))
    return result.view.stored.task


@pytest.mark.parametrize(
    ("changes", "attribute", "expected"),
    [
        (TaskChanges(title="New title"), "title", "New title"),
        (TaskChanges(description="new description"), "description", "new description"),
        (TaskChanges(category=Category.PERSONAL), "category", Category.PERSONAL),
        (TaskChanges(priority=Priority.HIGH), "priority", Priority.HIGH),
        (TaskChanges(estimate_minutes=45), "estimate_minutes", 45),
        (TaskChanges(deadline=NEW_DEADLINE), "deadline", NEW_DEADLINE),
        (TaskChanges(scheduled=NEW_SCHEDULE), "scheduled", NEW_SCHEDULE),
    ],
)
async def test_changes_only_the_given_field(
    changes: TaskChanges,
    attribute: str,
    expected: object,
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """A change updates its field, sets version 2, and stamps updated_at (ADR 0002 item 4)."""
    task = await _create_full_task(uow_factory, clock, ids)

    view = await edit_task(uow_factory, clock, task.id, 1, changes)

    assert getattr(view.stored.task, attribute) == expected
    assert view.stored.version == 2
    assert view.stored.task.updated_at == clock.now()


@pytest.mark.parametrize(
    ("changes", "attribute"),
    [
        (TaskChanges(description=None), "description"),
        (TaskChanges(category=None), "category"),
        (TaskChanges(priority=None), "priority"),
        (TaskChanges(estimate_minutes=None), "estimate_minutes"),
        (TaskChanges(deadline=None), "deadline"),
        (TaskChanges(scheduled=None), "scheduled"),
    ],
)
async def test_none_clears_the_field(
    changes: TaskChanges,
    attribute: str,
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """``None`` clears an optional field (ADR 0001 item 12)."""
    task = await _create_full_task(uow_factory, clock, ids)

    view = await edit_task(uow_factory, clock, task.id, 1, changes)

    assert getattr(view.stored.task, attribute) is None


@pytest.mark.parametrize(
    "attribute",
    [
        "title",
        "description",
        "category",
        "priority",
        "estimate_minutes",
        "deadline",
        "scheduled",
    ],
)
async def test_unset_keeps_the_field(
    attribute: str,
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """``UNSET`` leaves a field unchanged (ADR 0001 item 12)."""
    task = await _create_full_task(uow_factory, clock, ids)
    changes = (
        TaskChanges(description="probe") if attribute == "title" else TaskChanges(title="New title")
    )

    view = await edit_task(uow_factory, clock, task.id, 1, changes)

    assert getattr(view.stored.task, attribute) == getattr(task, attribute)


@given(
    edited=st.sampled_from(["deadline", "scheduled", "estimate_minutes"]),
    new_deadline=_NEW_DEADLINE,
    new_schedule=_NEW_SCHEDULE,
    new_estimate=_NEW_ESTIMATE,
)
def test_editing_one_of_the_three_keeps_the_other_two(
    edited: str,
    new_deadline: DateDeadline | None,
    new_schedule: TimeInterval | None,
    new_estimate: int | None,
) -> None:
    """Deadline, schedule, and estimate are independent (ADR 0001 item 12)."""
    store = InMemoryStore()
    ids = SequentialIdGenerator()
    clock = FakeClock()

    def factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(store)

    asyncio.run(
        _edit_one_of_three(
            factory,
            clock,
            ids,
            edited,
            new_deadline,
            new_schedule,
            new_estimate,
        )
    )


async def _edit_one_of_three(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    edited: str,
    new_deadline: DateDeadline | None,
    new_schedule: TimeInterval | None,
    new_estimate: int | None,
) -> None:
    """Edit one of the three fields and assert the other two are untouched."""
    task = await _create_full_task(uow_factory, clock, ids)
    changes = _changes_for(edited, new_deadline, new_schedule, new_estimate)

    view = await edit_task(uow_factory, clock, task.id, 1, changes)

    after = view.stored.task
    if edited == "deadline":
        assert after.deadline == new_deadline
        assert after.scheduled == task.scheduled
        assert after.estimate_minutes == task.estimate_minutes
    elif edited == "scheduled":
        assert after.scheduled == new_schedule
        assert after.deadline == task.deadline
        assert after.estimate_minutes == task.estimate_minutes
    else:
        assert after.estimate_minutes == new_estimate
        assert after.deadline == task.deadline
        assert after.scheduled == task.scheduled


def _changes_for(
    edited: str,
    new_deadline: DateDeadline | None,
    new_schedule: TimeInterval | None,
    new_estimate: int | None,
) -> TaskChanges:
    """Build the single-field changes for the property test."""
    if edited == "deadline":
        return TaskChanges(deadline=new_deadline)
    if edited == "scheduled":
        return TaskChanges(scheduled=new_schedule)
    return TaskChanges(estimate_minutes=new_estimate)


@pytest.mark.parametrize(
    ("changes", "field"),
    [
        (TaskChanges(title="   "), "title"),
        (TaskChanges(estimate_minutes=0), "estimate_minutes"),
    ],
)
async def test_invalid_edits_are_rejected_and_change_nothing(
    changes: TaskChanges,
    field: str,
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    store: InMemoryStore,
) -> None:
    """A domain rejection keeps the stored task and its version (ADR 0002 items 2 and 17)."""
    task = await _create_full_task(uow_factory, clock, ids)

    with pytest.raises(ValidationFailedError) as error:
        await edit_task(uow_factory, clock, task.id, 1, changes)

    assert error.value.field == field
    assert store.tasks[task.id].version == 1
    assert store.tasks[task.id].task == task


async def test_stale_version_is_rejected_and_changes_nothing(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    store: InMemoryStore,
) -> None:
    """A stale version reports both versions and writes nothing (ADR 0002 item 4)."""
    task = await _create_full_task(uow_factory, clock, ids)

    with pytest.raises(StaleVersionError) as error:
        await edit_task(uow_factory, clock, task.id, 7, TaskChanges(title="New title"))

    assert error.value.expected_version == 7
    assert error.value.current_version == 1
    assert store.tasks[task.id].version == 1
    assert store.tasks[task.id].task.title == "Old title"


async def test_missing_task_is_not_found(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
) -> None:
    """Editing an unknown task raises NotFoundError (ADR 0002 item 5)."""
    with pytest.raises(NotFoundError):
        await edit_task(uow_factory, clock, UUID(int=99), 1, TaskChanges(title="New title"))


async def test_deleted_task_is_not_found(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """Editing a soft deleted task raises NotFoundError (ADR 0002 item 5)."""
    task = await _create_full_task(uow_factory, clock, ids)
    await delete_task(uow_factory, clock, task.id, 1)

    with pytest.raises(NotFoundError):
        await edit_task(uow_factory, clock, task.id, 2, TaskChanges(title="New title"))


async def test_all_unset_changes_are_rejected(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    store: InMemoryStore,
) -> None:
    """An empty change set is a validation failure without a field (ADR 0002 item 17)."""
    task = await _create_full_task(uow_factory, clock, ids)

    with pytest.raises(ValidationFailedError) as error:
        await edit_task(uow_factory, clock, task.id, 1, TaskChanges())

    assert error.value.message == "no changes given"
    assert error.value.field is None
    assert store.tasks[task.id].version == 1
