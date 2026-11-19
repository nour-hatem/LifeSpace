"""Database engine, shared metadata, and readiness probe.

This layer owns SQLAlchemy and asyncpg. It must not import ``lifespace.api``,
and it must never log connection URLs or credentials.
"""

import asyncio
import logging

from sqlalchemy import MetaData, event, text
from sqlalchemy.engine import ExceptionContext
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)

_DETAIL_SEPARATOR = "\nDETAIL:"

READINESS_TIMEOUT_SECONDS = 3.0

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


class _RedactedDatabaseError(Exception):
    """A database error whose message omits PostgreSQL row values (ADR 0002 item 23)."""


def _sanitize_database_error(context: ExceptionContext) -> None:
    """Remove PostgreSQL row values from a database error (ADR 0002 item 23).

    PostgreSQL appends a ``DETAIL`` line with the failing row, which can contain
    task content. The SQLAlchemy wrapper copies the original message into its
    arguments before this event runs, so both the wrapper message and ``orig``
    are reduced to the part before ``DETAIL``. The constraint name is kept so
    callers can still classify the error.
    """
    wrapped = context.sqlalchemy_exception
    if wrapped is None or not wrapped.args or not isinstance(wrapped.args[0], str):
        return
    message = wrapped.args[0]
    if _DETAIL_SEPARATOR not in message:
        return
    wrapped.args = (message.split(_DETAIL_SEPARATOR, 1)[0],)
    if wrapped.orig is not None:
        original = str(wrapped.orig).split(_DETAIL_SEPARATOR, 1)[0]
        wrapped.orig = _RedactedDatabaseError(original)


def create_engine(url: str) -> AsyncEngine:
    """Create the async engine, hiding statement parameters in errors (ADR 0002 item 23)."""
    engine = create_async_engine(url, pool_pre_ping=True, hide_parameters=True)
    event.listen(engine.sync_engine, "handle_error", _sanitize_database_error)
    return engine


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create sessions that keep their loaded values after a commit (ADR 0002 item 2)."""
    return async_sessionmaker(engine, expire_on_commit=False)


async def check_database(engine: AsyncEngine) -> bool:
    """Return whether a trivial query succeeds within the readiness timeout."""
    try:
        async with asyncio.timeout(READINESS_TIMEOUT_SECONDS):
            async with engine.connect() as connection:
                await connection.execute(text("select 1"))
        return True
    except Exception as exc:  # noqa: BLE001 - a health probe reports any failure as unavailable
        logger.warning("Database readiness check failed: %s", type(exc).__name__)
        return False
