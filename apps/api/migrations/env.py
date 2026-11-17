"""Alembic environment for LifeSpace.

The async template is used because the application runs on SQLAlchemy's
asyncio engine. The database URL comes from the Alembic configuration when it
is set, otherwise from the application settings. The URL is never logged or
printed.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from lifespace.config import Settings
from lifespace.infrastructure import models  # noqa: F401  (register the tables)
from lifespace.infrastructure.db import metadata

config = context.config

if config.config_file_name is not None:
    # Keep application loggers enabled when migrations run in-process (tests).
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = metadata


def _resolved_url() -> str:
    """Return the configured URL, falling back to the application settings."""
    configured = config.get_main_option("sqlalchemy.url")
    if configured:
        return configured
    return Settings().database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=_resolved_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run the migrations on an established connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create the migration engine, run the migrations, and dispose it."""
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _resolved_url()
    connectable = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
