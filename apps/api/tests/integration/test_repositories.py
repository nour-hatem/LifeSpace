"""Integration tests for the SQLAlchemy repositories (ADR 0002 items 3 to 8, 14 to 16)."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterator
from dataclasses import fields
from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid7
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from lifespace.application.errors import (
    IdempotencyInProgressError,
    InvalidCursorError,
    NotFoundError,
    StaleVersionError,
)
from lifespace.application.models import (
    CreateTaskCommand,
    IdempotencyInput,
    IdempotencyRecord,
    StoredTask,
    TaskChanges,
    TaskFilter,
)
from lifespace.application.ports import UnitOfWorkFactory
from lifespace.application.tasks import (
    create_task,
    delete_task,
    edit_task,
    get_task,
    list_task_events,
    list_tasks,
    transition_task,
)
from lifespace.domain.deadline import DateDeadline, DateTimeDeadline, Deadline
from lifespace.domain.lifecycle import StatusEvent
from lifespace.domain.lifecycle import transition_task as domain_transition_task
from lifespace.domain.task import Category, Priority, Task, TaskSource, TaskStatus
from lifespace.domain.task import create_task as domain_create_task
from lifespace.domain.task import edit_task as domain_edit_task
from lifespace.domain.time import TimeInterval, as_instant
from lifespace.infrastructure.cursor import encode_cursor
from lifespace.infrastructure.db import create_engine, create_session_factory
from lifespace.infrastructure.models import AppSettingsRow, StatusEventRow
from lifespace.infrastructure.system import SystemClock, Uuid7Generator
from lifespace.infrastructure.unit_of_work import create_unit_of_work_factory
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
def uow_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> UnitOfWorkFactory:
    """Return a real unit of work factory over the test database."""
    return create_unit_of_work_factory(session_factory)


def _new_task(
    *,
    title: str = "Task",
    task_id: UUID | None = None,
    now: datetime = NOW,
    status: TaskStatus = TaskStatus.PLANNED,
    source: TaskSource = TaskSource.MANUAL,
    description: str | None = None,
    category: Category | None = None,
    priority: Priority | None = None,
    estimate_minutes: int | None = None,
    deadline: Deadline | None = None,
    scheduled: TimeInterval | None = None,
) -> Task:
    """Build a valid domain task for the repository tests."""
    return domain_create_task(
        task_id=task_id if task_id is not None else uuid7(),
        title=title,
        now=now,
        status=status,
        source=source,
        description=description,
        category=category,
        priority=priority,
        estimate_minutes=estimate_minutes,
        deadline=deadline,
        scheduled=scheduled,
    )


def _assert_same_task(actual: Task, expected: Task) -> None:
    """Compare every field, comparing datetimes as UTC instants (ADR 0001 item 19)."""
    for field in fields(Task):
        left = getattr(actual, field.name)
        right = getattr(expected, field.name)
        if isinstance(right, datetime):
            assert as_instant(left) == as_instant(right), field.name
        elif field.name == "deadline":
            if right is None:
                assert left is None
            elif isinstance(right, DateTimeDeadline):
                assert isinstance(left, DateTimeDeadline)
                assert as_instant(left.at) == as_instant(right.at)
            else:
                assert left == right
        elif field.name == "scheduled":
            if right is None:
                assert left is None
            else:
                assert left is not None
                assert as_instant(left.start) == as_instant(right.start)
                assert as_instant(left.end) == as_instant(right.end)
        else:
            assert left == right, field.name


@pytest.mark.parametrize(
    "deadline",
    [
        DateDeadline(day=date(2026, 12, 1)),
        DateTimeDeadline(at=datetime(2026, 10, 29, 23, 30, tzinfo=ZoneInfo("Africa/Cairo"))),
    ],
)
async def test_add_and_get_round_trip(
    uow_factory: UnitOfWorkFactory,
    deadline: Deadline,
) -> None:
    """A task with a deadline, schedule, category, and priority round trips (ADR 0002 item 3)."""
    cairo = ZoneInfo("Africa/Cairo")
    task = _new_task(
        title="Round trip",
        description="details",
        category=Category.WORK,
        priority=Priority.HIGH,
        estimate_minutes=45,
        deadline=deadline,
        scheduled=TimeInterval(
            start=datetime(2026, 4, 23, 9, tzinfo=cairo),
            end=datetime(2026, 4, 23, 10, 30, tzinfo=cairo),
        ),
    )

    async with uow_factory() as uow:
        stored = await uow.tasks.add(task)
        await uow.commit()
    assert stored.version == 1

    async with uow_factory() as uow:
        loaded = await uow.tasks.get(task.id)

    assert loaded is not None
    assert loaded.version == 1
    _assert_same_task(loaded.task, task)


async def test_save_increments_the_version_and_updates_columns(
    uow_factory: UnitOfWorkFactory,
) -> None:
    """A guarded save writes every mutable column and returns the next version (ADR 0002 item 4)."""
    task = _new_task(title="Before")
    async with uow_factory() as uow:
        await uow.tasks.add(task)
        await uow.commit()

    async with uow_factory() as uow:
        loaded = await uow.tasks.get(task.id)
        assert loaded is not None
        edited = domain_edit_task(
            loaded.task,
            now=NOW + timedelta(minutes=1),
            title="After",
            estimate_minutes=30,
            priority=Priority.LOW,
        )
        saved = await uow.tasks.save(edited, expected_version=1)
        await uow.commit()

    assert saved.version == 2
    async with uow_factory() as uow:
        reloaded = await uow.tasks.get(task.id)
    assert reloaded is not None
    assert reloaded.version == 2
    assert reloaded.task.title == "After"
    assert reloaded.task.estimate_minutes == 30
    assert reloaded.task.priority is Priority.LOW


async def test_concurrent_saves_allow_exactly_one_winner(
    uow_factory: UnitOfWorkFactory,
) -> None:
    """Two transactions saving one version race: one wins, one is stale (ADR 0002 item 4)."""
    task = _new_task(title="Contended")
    async with uow_factory() as uow:
        await uow.tasks.add(task)
        await uow.commit()

    barrier = asyncio.Barrier(2)

    async def attempt(title: str) -> StoredTask:
        async with uow_factory() as uow:
            loaded = await uow.tasks.get(task.id)
            assert loaded is not None
            await barrier.wait()
            edited = domain_edit_task(
                loaded.task,
                now=NOW + timedelta(minutes=1),
                title=title,
            )
            saved = await uow.tasks.save(edited, expected_version=1)
            await uow.commit()
            return saved

    results = await asyncio.gather(attempt("A"), attempt("B"), return_exceptions=True)

    successes = [result for result in results if isinstance(result, StoredTask)]
    failures = [result for result in results if isinstance(result, StaleVersionError)]
    assert len(successes) == 1
    assert len(failures) == 1
    assert failures[0].current_version == 2

    async with uow_factory() as uow:
        loaded = await uow.tasks.get(task.id)
    assert loaded is not None
    assert loaded.version == 2


async def test_guarded_updates_report_the_reason(uow_factory: UnitOfWorkFactory) -> None:
    """Missing and deleted tasks are not found; an old version is stale (ADR 0002 items 4 and 5)."""
    task = _new_task()

    async with uow_factory() as uow:
        await uow.tasks.add(task)
        await uow.commit()

    with pytest.raises(StaleVersionError) as stale_save:
        async with uow_factory() as uow:
            await uow.tasks.save(task, expected_version=9)
    assert stale_save.value.current_version == 1

    with pytest.raises(StaleVersionError) as stale_delete:
        async with uow_factory() as uow:
            await uow.tasks.soft_delete(task.id, expected_version=9, now=NOW)
    assert stale_delete.value.current_version == 1

    with pytest.raises(NotFoundError):
        async with uow_factory() as uow:
            await uow.tasks.save(_new_task(task_id=UUID(int=9999)), expected_version=1)
    with pytest.raises(NotFoundError):
        async with uow_factory() as uow:
            await uow.tasks.soft_delete(UUID(int=9999), expected_version=1, now=NOW)

    async with uow_factory() as uow:
        await uow.tasks.soft_delete(task.id, expected_version=1, now=NOW)
        await uow.commit()

    with pytest.raises(NotFoundError):
        async with uow_factory() as uow:
            await uow.tasks.save(task, expected_version=2)
    with pytest.raises(NotFoundError):
        async with uow_factory() as uow:
            await uow.tasks.soft_delete(task.id, expected_version=2, now=NOW)


async def test_soft_delete_hides_the_task_but_keeps_its_events(
    uow_factory: UnitOfWorkFactory,
    engine: AsyncEngine,
) -> None:
    """A deleted task is invisible to reads while its history stays stored (ADR 0002 item 5)."""
    task = _new_task()
    event = StatusEvent(
        task_id=task.id,
        from_status=TaskStatus.PLANNED,
        to_status=TaskStatus.IN_PROGRESS,
        occurred_at=NOW,
    )

    async with uow_factory() as uow:
        await uow.tasks.add(task)
        await uow.tasks.add_event(uuid7(), event)
        await uow.tasks.soft_delete(task.id, expected_version=1, now=NOW + timedelta(minutes=1))
        await uow.commit()

    async with uow_factory() as uow:
        assert await uow.tasks.get(task.id) is None
        page = await uow.tasks.list(TaskFilter(), limit=10)
    assert page.items == ()
    assert page.next_cursor is None

    async with engine.connect() as connection:
        count = await connection.scalar(
            select(func.count())
            .select_from(StatusEventRow)
            .where(StatusEventRow.task_id == task.id)
        )
    assert count == 1


async def test_task_pagination_is_stable(uow_factory: UnitOfWorkFactory) -> None:
    """Twenty-five tasks page by ten without gaps or duplicates (ADR 0002 item 15)."""
    base = datetime(2026, 2, 1, 12, tzinfo=UTC)
    tasks = [
        _new_task(
            task_id=UUID(int=1000 + index),
            title=f"Task {index}",
            now=base if index < 5 else base + timedelta(minutes=index),
        )
        for index in range(25)
    ]
    async with uow_factory() as uow:
        for task in tasks:
            await uow.tasks.add(task)
        await uow.commit()

    seen: list[UUID] = []
    keys: list[tuple[datetime, UUID]] = []
    cursor: str | None = None
    pages = 0
    while True:
        async with uow_factory() as uow:
            page = await uow.tasks.list(TaskFilter(), limit=10, cursor=cursor)
        pages += 1
        seen.extend(stored.task.id for stored in page.items)
        keys.extend((as_instant(stored.task.created_at), stored.task.id) for stored in page.items)
        cursor = page.next_cursor
        if cursor is None:
            break

    assert pages == 3
    assert len(seen) == 25
    assert len(set(seen)) == 25
    assert set(seen) == {task.id for task in tasks}
    assert keys == sorted(keys, reverse=True)


async def test_event_pagination_is_stable(uow_factory: UnitOfWorkFactory) -> None:
    """Events page by ten with the same ordering guarantees as tasks (ADR 0002 item 15)."""
    task = _new_task()
    base = datetime(2026, 2, 1, 12, tzinfo=UTC)
    event_ids = [UUID(int=2000 + index) for index in range(25)]

    async with uow_factory() as uow:
        await uow.tasks.add(task)
        for index, event_id in enumerate(event_ids):
            occurred_at = base if index < 5 else base + timedelta(minutes=index)
            await uow.tasks.add_event(
                event_id,
                StatusEvent(
                    task_id=task.id,
                    from_status=TaskStatus.PLANNED,
                    to_status=TaskStatus.IN_PROGRESS,
                    occurred_at=occurred_at,
                ),
            )
        await uow.commit()

    seen: list[UUID] = []
    keys: list[tuple[datetime, UUID]] = []
    cursor: str | None = None
    pages = 0
    while True:
        async with uow_factory() as uow:
            page = await uow.tasks.list_events(task.id, limit=10, cursor=cursor)
        pages += 1
        seen.extend(stored.id for stored in page.items)
        keys.extend((as_instant(stored.event.occurred_at), stored.id) for stored in page.items)
        cursor = page.next_cursor
        if cursor is None:
            break

    assert pages == 3
    assert len(seen) == 25
    assert set(seen) == set(event_ids)
    assert keys == sorted(keys, reverse=True)


@pytest.mark.parametrize(
    "cursor",
    [
        "not-base64!",
        encode_cursor(["only-one"]),
        encode_cursor(["2026-01-01T00:00:00+00:00", "not-a-uuid"]),
        encode_cursor(["not-an-instant", "00000000-0000-0000-0000-000000000001"]),
        encode_cursor(["2026-01-01T00:00:00", "00000000-0000-0000-0000-000000000001"]),
    ],
)
async def test_malformed_task_cursors_are_rejected(
    uow_factory: UnitOfWorkFactory,
    cursor: str,
) -> None:
    """A malformed cursor raises ``InvalidCursorError`` instead of a database error."""
    with pytest.raises(InvalidCursorError):
        async with uow_factory() as uow:
            await uow.tasks.list(TaskFilter(), limit=10, cursor=cursor)


async def test_a_malformed_event_cursor_is_rejected(uow_factory: UnitOfWorkFactory) -> None:
    """The event list rejects a malformed cursor too (ADR 0002 item 15)."""
    task = _new_task()
    async with uow_factory() as uow:
        await uow.tasks.add(task)
        await uow.commit()

    with pytest.raises(InvalidCursorError):
        async with uow_factory() as uow:
            await uow.tasks.list_events(task.id, limit=10, cursor="not-base64!")


async def test_filters_match_the_in_memory_fake(uow_factory: UnitOfWorkFactory) -> None:
    """Status, category, priority, and combinations filter like the fake (ADR 0002 item 16)."""
    planned_work = _new_task(title="planned work", category=Category.WORK, priority=Priority.HIGH)
    planned_personal = _new_task(
        title="planned personal", category=Category.PERSONAL, priority=Priority.LOW
    )
    inbox_work = _new_task(
        title="inbox work",
        status=TaskStatus.INBOX,
        category=Category.WORK,
        priority=Priority.HIGH,
    )
    completed_work = domain_transition_task(
        _new_task(title="completed work", category=Category.WORK, priority=Priority.HIGH),
        TaskStatus.COMPLETED,
        now=NOW,
    ).task
    canceled_personal = domain_transition_task(
        _new_task(
            title="canceled personal",
            category=Category.PERSONAL,
            priority=Priority.HIGH,
        ),
        TaskStatus.CANCELED,
        now=NOW,
        reason="dropped",
    ).task
    tasks = [
        planned_work,
        planned_personal,
        inbox_work,
        completed_work,
        canceled_personal,
    ]

    async with uow_factory() as uow:
        for task in tasks:
            await uow.tasks.add(task)
        await uow.commit()

    async def listed(task_filter: TaskFilter) -> set[UUID]:
        async with uow_factory() as uow:
            page = await uow.tasks.list(task_filter, limit=200)
        return {stored.task.id for stored in page.items}

    assert await listed(TaskFilter()) == {task.id for task in tasks}
    assert await listed(TaskFilter(statuses=frozenset({TaskStatus.PLANNED}))) == {
        planned_work.id,
        planned_personal.id,
    }
    assert await listed(
        TaskFilter(statuses=frozenset({TaskStatus.INBOX, TaskStatus.COMPLETED}))
    ) == {inbox_work.id, completed_work.id}
    assert await listed(TaskFilter(category=Category.WORK)) == {
        planned_work.id,
        inbox_work.id,
        completed_work.id,
    }
    assert await listed(TaskFilter(priority=Priority.HIGH)) == {
        planned_work.id,
        inbox_work.id,
        completed_work.id,
        canceled_personal.id,
    }
    assert await listed(
        TaskFilter(
            statuses=frozenset({TaskStatus.PLANNED, TaskStatus.COMPLETED}),
            category=Category.WORK,
            priority=Priority.HIGH,
        )
    ) == {planned_work.id, completed_work.id}


async def test_settings_round_trip(
    uow_factory: UnitOfWorkFactory,
    engine: AsyncEngine,
) -> None:
    """The settings row starts at UTC and stores a new zone with its instant (ADR 0002 item 8)."""
    async with uow_factory() as uow:
        assert await uow.settings.get_timezone() == "UTC"
        await uow.settings.set_timezone("Africa/Cairo", now=NOW)
        await uow.commit()

    async with uow_factory() as uow:
        assert await uow.settings.get_timezone() == "Africa/Cairo"

    async with engine.connect() as connection:
        updated_at = await connection.scalar(
            select(AppSettingsRow.updated_at).where(AppSettingsRow.id == 1)
        )
    assert updated_at == as_instant(NOW)


async def test_idempotency_records_round_trip_and_reject_duplicates(
    uow_factory: UnitOfWorkFactory,
) -> None:
    """A key is stored once; a duplicate keeps the unit of work usable (ADR 0002 item 14)."""
    task = _new_task()
    record = IdempotencyRecord(
        key="key-1",
        request_fingerprint="fingerprint",
        task_id=task.id,
    )
    async with uow_factory() as uow:
        await uow.tasks.add(task)
        await uow.idempotency.add(record, now=NOW)
        await uow.commit()

    async with uow_factory() as uow:
        assert await uow.idempotency.get("key-1") == record

        with pytest.raises(IdempotencyInProgressError):
            await uow.idempotency.add(record, now=NOW)

        assert await uow.idempotency.get("key-1") == record
        await uow.commit()


async def test_an_idempotency_key_restricts_task_deletion(
    uow_factory: UnitOfWorkFactory,
    engine: AsyncEngine,
) -> None:
    """The idempotency foreign key prevents a hard delete of its task (ADR 0002 item 14)."""
    task = _new_task()
    async with uow_factory() as uow:
        await uow.tasks.add(task)
        await uow.idempotency.add(
            IdempotencyRecord(key="key-1", request_fingerprint="fp", task_id=task.id),
            now=NOW,
        )
        await uow.commit()

    with pytest.raises(IntegrityError):
        async with engine.begin() as connection:
            await connection.execute(
                text("delete from tasks where id = :task_id"),
                {"task_id": task.id},
            )


async def test_an_event_requires_an_existing_task(uow_factory: UnitOfWorkFactory) -> None:
    """The event foreign key rejects an event without its task (ADR 0002 item 6)."""
    event = StatusEvent(
        task_id=UUID(int=9999),
        from_status=TaskStatus.PLANNED,
        to_status=TaskStatus.IN_PROGRESS,
        occurred_at=NOW,
    )

    with pytest.raises(IntegrityError):
        async with uow_factory() as uow:
            await uow.tasks.add_event(uuid7(), event)


async def test_the_use_cases_run_end_to_end(uow_factory: UnitOfWorkFactory) -> None:
    """Create, replay, edit, transition, list, and delete through the real adapters."""
    clock = SystemClock()
    ids = Uuid7Generator()

    created = await create_task(
        uow_factory,
        clock,
        ids,
        CreateTaskCommand(
            title="End to end",
            priority=Priority.HIGH,
            deadline=DateDeadline(day=date(2026, 12, 1)),
        ),
        idempotency=IdempotencyInput(key="end-to-end", fingerprint="fingerprint"),
    )
    task_id = created.view.stored.task.id
    assert created.replayed is False
    assert created.view.stored.version == 1

    replayed = await create_task(
        uow_factory,
        clock,
        ids,
        CreateTaskCommand(
            title="End to end",
            priority=Priority.HIGH,
            deadline=DateDeadline(day=date(2026, 12, 1)),
        ),
        idempotency=IdempotencyInput(key="end-to-end", fingerprint="fingerprint"),
    )
    assert replayed.replayed is True
    assert replayed.view.stored.task.id == task_id

    got = await get_task(uow_factory, clock, task_id)
    assert got.stored.task.title == "End to end"

    edited = await edit_task(
        uow_factory,
        clock,
        task_id,
        1,
        TaskChanges(title="Edited", estimate_minutes=30),
    )
    assert edited.stored.version == 2
    assert edited.stored.task.estimate_minutes == 30

    started = await transition_task(
        uow_factory,
        clock,
        ids,
        task_id,
        TaskStatus.IN_PROGRESS,
        2,
    )
    assert started.stored.version == 3
    assert started.stored.task.status is TaskStatus.IN_PROGRESS

    page = await list_tasks(uow_factory, clock, TaskFilter(), limit=10)
    assert [view.stored.task.id for view in page.items] == [task_id]

    events = await list_task_events(uow_factory, task_id, limit=10)
    assert [stored.event.to_status for stored in events.items] == [TaskStatus.IN_PROGRESS]

    completed = await transition_task(
        uow_factory,
        clock,
        ids,
        task_id,
        TaskStatus.COMPLETED,
        3,
    )
    assert completed.stored.task.status is TaskStatus.COMPLETED

    await delete_task(uow_factory, clock, task_id, 4)
    with pytest.raises(NotFoundError):
        await get_task(uow_factory, clock, task_id)
