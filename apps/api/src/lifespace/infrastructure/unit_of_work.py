"""One SQLAlchemy transaction per unit of work (ADR 0002 item 2)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from lifespace.application.ports import (
    IdempotencyRepository,
    SettingsRepository,
    TaskRepository,
    UnitOfWorkFactory,
)
from lifespace.infrastructure.repositories import (
    SqlAlchemyIdempotencyRepository,
    SqlAlchemySettingsRepository,
    SqlAlchemyTaskRepository,
)


class SqlAlchemyUnitOfWork:
    """A single-use transaction exposing the three repositories (ADR 0002 item 2)."""

    tasks: TaskRepository
    settings: SettingsRepository
    idempotency: IdempotencyRepository

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self._used = False
        self._committed = False

    async def __aenter__(self) -> SqlAlchemyUnitOfWork:
        """Open a session and begin its transaction (ADR 0002 item 2)."""
        if self._used:
            raise RuntimeError("the unit of work is single use")
        self._used = True
        session = self._session_factory()
        try:
            await session.begin()
        except BaseException:
            await session.close()
            raise
        self._session = session
        self._committed = False
        self.tasks = SqlAlchemyTaskRepository(session)
        self.settings = SqlAlchemySettingsRepository(session)
        self.idempotency = SqlAlchemyIdempotencyRepository(session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object | None,
    ) -> None:
        """Roll back uncommitted work and always close the session (ADR 0002 item 2)."""
        session = self._active_session()
        try:
            if exc_type is not None or not self._committed:
                await session.rollback()
        finally:
            await session.close()
            self._session = None

    async def commit(self) -> None:
        """Commit the transaction (ADR 0002 item 2)."""
        await self._active_session().commit()
        self._committed = True

    async def rollback(self) -> None:
        """Discard every change in the transaction (ADR 0002 item 2)."""
        await self._active_session().rollback()
        self._committed = False

    def _active_session(self) -> AsyncSession:
        """Return the open session or reject a unit of work used outside its block."""
        if self._session is None:
            raise RuntimeError("the unit of work is not active")
        return self._session


def create_unit_of_work_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> UnitOfWorkFactory:
    """Return a factory that opens a fresh unit of work per call (ADR 0002 item 2)."""

    def create() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    return create
