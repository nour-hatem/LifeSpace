"""Regression tests for input bounds, commit order, and version checks (ADR 0002 items 20 to 24)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID
from zoneinfo import ZoneInfoNotFoundError

import pytest

from lifespace.application.errors import ValidationFailedError
from lifespace.application.models import (
    CreateTaskCommand,
    IdempotencyInput,
    TaskChanges,
    TaskFilter,
)
from lifespace.application.ports import UnitOfWorkFactory
from lifespace.application.settings import update_timezone
from lifespace.application.tasks import (
    create_task,
    delete_task,
    edit_task,
    list_tasks,
    transition_task,
)
from lifespace.domain.deadline import DateDeadline
from lifespace.domain.task import TaskStatus
from tests.unit.application.fakes import (
    FakeClock,
    InMemoryStore,
    InMemoryUnitOfWork,
    SequentialIdGenerator,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _forbidden_factory() -> UnitOfWorkFactory:
    """Return a factory that fails if a use case opens a unit of work."""

    def create() -> InMemoryUnitOfWork:
        raise AssertionError("the unit of work must not be opened")

    return create


def _poison_deadline() -> DateDeadline:
    """Return a DateDeadline as it could exist in a row written before the range check."""
    deadline = DateDeadline(day=date(2026, 1, 1))
    object.__setattr__(deadline, "day", date(9999, 12, 31))
    return deadline


async def _existing_task(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> UUID:
    """Create one planned task and return its id."""
    result = await create_task(uow_factory, clock, ids, CreateTaskCommand(title="Task"))
    return result.view.stored.task.id


async def test_create_builds_the_view_before_commit(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    store: InMemoryStore,
) -> None:
    """A failure while rendering leaves the created task uncommitted (ADR 0002 item 22)."""
    store.timezone = "Invalid/Zone"

    with pytest.raises(ZoneInfoNotFoundError):
        await create_task(uow_factory, clock, ids, CreateTaskCommand(title="Task"))

    assert store.tasks == {}
    assert store.events == {}
    assert store.idempotency == {}


async def test_keyed_create_builds_the_view_before_commit(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    store: InMemoryStore,
) -> None:
    """A keyed create also writes nothing when rendering fails (ADR 0002 item 22)."""
    store.timezone = "Invalid/Zone"

    with pytest.raises(ZoneInfoNotFoundError):
        await create_task(
            uow_factory,
            clock,
            ids,
            CreateTaskCommand(title="Task"),
            idempotency=IdempotencyInput(key="key-1", fingerprint="fingerprint"),
        )

    assert store.tasks == {}
    assert store.events == {}
    assert store.idempotency == {}


async def test_edit_builds_the_view_before_commit(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    store: InMemoryStore,
) -> None:
    """A failed edit leaves the old task and version in place (ADR 0002 item 22)."""
    task_id = await _existing_task(uow_factory, clock, ids)
    store.timezone = "Invalid/Zone"

    with pytest.raises(ZoneInfoNotFoundError):
        await edit_task(uow_factory, clock, task_id, 1, TaskChanges(title="Changed"))

    stored = store.tasks[task_id]
    assert stored.task.title == "Task"
    assert stored.version == 1
    assert store.events == {}


async def test_transition_builds_the_view_before_commit(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    store: InMemoryStore,
) -> None:
    """A failed transition leaves the task and its history unchanged (ADR 0002 item 22)."""
    task_id = await _existing_task(uow_factory, clock, ids)
    store.timezone = "Invalid/Zone"

    with pytest.raises(ZoneInfoNotFoundError):
        await transition_task(
            uow_factory,
            clock,
            ids,
            task_id,
            TaskStatus.IN_PROGRESS,
            1,
        )

    stored = store.tasks[task_id]
    assert stored.task.status is TaskStatus.PLANNED
    assert stored.version == 1
    assert store.events == {}


async def test_a_poison_deadline_commits_nothing_and_the_list_still_works(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    store: InMemoryStore,
) -> None:
    """A poison 9999-12-31 deadline cannot poison the stored list (ADR 0002 item 22)."""
    earlier = await _existing_task(uow_factory, clock, ids)

    with pytest.raises(OverflowError):
        await create_task(
            uow_factory,
            clock,
            ids,
            CreateTaskCommand(title="Poison", deadline=_poison_deadline()),
        )

    assert set(store.tasks) == {earlier}
    page = await list_tasks(uow_factory, clock, TaskFilter(), limit=10)
    assert [view.stored.task.id for view in page.items] == [earlier]


@pytest.mark.parametrize("title", ["bad\x00title", "a" * 501])
async def test_create_rejects_text_the_database_cannot_store(
    title: str,
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    store: InMemoryStore,
) -> None:
    """NUL text and oversized titles are validation failures and store nothing."""
    with pytest.raises(ValidationFailedError) as error:
        await create_task(uow_factory, clock, ids, CreateTaskCommand(title=title))

    assert error.value.field == "title"
    assert store.tasks == {}


async def test_create_rejects_a_nul_description(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    store: InMemoryStore,
) -> None:
    """A NUL character in the description is a validation failure."""
    with pytest.raises(ValidationFailedError) as error:
        await create_task(
            uow_factory,
            clock,
            ids,
            CreateTaskCommand(title="Task", description="bad\x00description"),
        )

    assert error.value.field == "description"
    assert store.tasks == {}


@pytest.mark.parametrize("version", [0, -1, 2**31])
async def test_edit_rejects_a_version_outside_the_storable_range(
    version: int,
    clock: FakeClock,
) -> None:
    """An edit version outside the range fails before any database access (ADR 0002 item 20)."""
    with pytest.raises(ValidationFailedError) as error:
        await edit_task(
            _forbidden_factory(),
            clock,
            UUID(int=1),
            version,
            TaskChanges(title="Changed"),
        )
    assert error.value.field == "version"


@pytest.mark.parametrize("version", [0, -1, 2**31])
async def test_delete_rejects_a_version_outside_the_storable_range(
    version: int,
    clock: FakeClock,
) -> None:
    """A delete version outside the range fails before any database access."""
    with pytest.raises(ValidationFailedError) as error:
        await delete_task(_forbidden_factory(), clock, UUID(int=1), version)
    assert error.value.field == "version"


@pytest.mark.parametrize("version", [0, -1, 2**31])
async def test_transition_rejects_a_version_outside_the_storable_range(
    version: int,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """A transition version outside the range fails before any database access."""
    with pytest.raises(ValidationFailedError) as error:
        await transition_task(
            _forbidden_factory(),
            clock,
            ids,
            UUID(int=1),
            TaskStatus.IN_PROGRESS,
            version,
        )
    assert error.value.field == "version"


@pytest.mark.parametrize("timezone", ["a" * 65, "UTC\x00"])
async def test_update_timezone_rejects_oversized_and_nul_names(
    timezone: str,
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    store: InMemoryStore,
) -> None:
    """A long or NUL time zone name fails with field timezone (ADR 0002 item 8)."""
    with pytest.raises(ValidationFailedError) as error:
        await update_timezone(uow_factory, clock, timezone)

    assert error.value.field == "timezone"
    assert store.timezone == "UTC"
