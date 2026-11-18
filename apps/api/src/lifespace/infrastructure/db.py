"""Database engine, shared metadata, and readiness probe.

This layer owns SQLAlchemy and asyncpg. It must not import ``lifespace.api``,
and it must never log connection URLs or credentials.
"""

import asyncio
import logging

from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)

READINESS_TIMEOUT_SECONDS = 3.0

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


def create_engine(url: str) -> AsyncEngine:
    """Create the async engine for the given SQLAlchemy URL."""
    return create_async_engine(url, pool_pre_ping=True)


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
