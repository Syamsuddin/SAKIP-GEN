"""Alembic env — async-aware, target = db.schema.metadata (tabel milik agen saja).

URL diresolusi dari: `-x db_url=...`, env ALEMBIC_DB_URL, env DB_STAGING_URL, atau
default SQLite (sqlite+aiosqlite). Memakai engine async agar cocok dengan driver
produksi (asyncmy) maupun uji (aiosqlite) tanpa driver sinkron tambahan.
"""
from __future__ import annotations

import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.schema import metadata  # noqa: E402

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = metadata


def _url() -> str:
    x = context.get_x_argument(as_dictionary=True)
    return (
        x.get("db_url")
        or os.getenv("ALEMBIC_DB_URL")
        or os.getenv("DB_STAGING_URL")
        or "sqlite+aiosqlite:///./alembic_dev.db"
    )


def _do_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def _run_async() -> None:
    engine = create_async_engine(_url(), poolclass=pool.NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(_do_migrations)
    await engine.dispose()


if context.is_offline_mode():
    context.configure(url=_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    asyncio.run(_run_async())
