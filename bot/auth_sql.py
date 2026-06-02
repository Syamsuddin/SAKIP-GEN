"""Repo autentikasi berbasis SQL (Fase 7) — pengganti in-memory untuk produksi.

Menyimpan pengguna & kode pendaftaran di tabel `bot_users` / `registration_codes`
(milik agen, lewat engine staging). Pendaftaran kode bersifat sekali-pakai. SQL
ditulis portabel (cek-lalu-insert/update) agar jalan di SQLite (uji) & MySQL (produksi).
"""
from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy import text

from bot.auth import User
from db.engines import get_staging_engine

AUTH_SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS bot_users (
    telegram_id INTEGER PRIMARY KEY,
    nama TEXT,
    peran TEXT DEFAULT 'operator',
    opd_ids TEXT,
    dibuat_pada TEXT
);
CREATE TABLE IF NOT EXISTS registration_codes (
    kode TEXT PRIMARY KEY,
    nama TEXT,
    peran TEXT DEFAULT 'operator',
    opd_ids TEXT,
    dipakai INTEGER DEFAULT 0,
    dipakai_oleh INTEGER,
    dipakai_pada TEXT
);
"""


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _opd(v) -> list[int]:
    if not v:
        return []
    return v if isinstance(v, list) else json.loads(v)


def _user(row) -> User:
    return User(
        telegram_id=row["telegram_id"], nama=row["nama"],
        peran=row["peran"] or "operator", opd_ids=_opd(row["opd_ids"]),
    )


class SqlAuthRepository:
    """Implementasi `AuthRepository` berbasis tabel SQL."""

    def __init__(self, engine=None) -> None:
        self._engine = engine

    def _eng(self):
        return self._engine or get_staging_engine()

    async def get_user(self, telegram_id: int) -> User | None:
        async with self._eng().connect() as c:
            row = (await c.execute(
                text("SELECT * FROM bot_users WHERE telegram_id = :t"), {"t": telegram_id}
            )).mappings().first()
        return _user(row) if row else None

    async def all_users(self) -> list[User]:
        async with self._eng().connect() as c:
            rows = (await c.execute(text("SELECT * FROM bot_users"))).mappings().all()
        return [_user(r) for r in rows]

    async def register(self, telegram_id: int, kode: str) -> User | None:
        async with self._eng().begin() as c:
            row = (await c.execute(
                text("SELECT * FROM registration_codes WHERE kode = :k AND dipakai = 0"),
                {"k": kode},
            )).mappings().first()
            if row is None:
                return None
            user = User(
                telegram_id=telegram_id, nama=row["nama"] or f"User {telegram_id}",
                peran=row["peran"] or "operator", opd_ids=_opd(row["opd_ids"]),
            )
            await c.execute(
                text("UPDATE registration_codes SET dipakai = 1, dipakai_oleh = :t, "
                     "dipakai_pada = :p WHERE kode = :k"),
                {"t": telegram_id, "p": _now(), "k": kode},
            )
            await self._simpan_user(c, user)
        return user

    async def tambah_kode(self, kode: str, nama: str = "", peran: str = "operator",
                          opd_ids: list[int] | None = None) -> None:
        async with self._eng().begin() as c:
            await c.execute(
                text("INSERT INTO registration_codes (kode, nama, peran, opd_ids, dipakai) "
                     "VALUES (:k, :n, :p, :o, 0)"),
                {"k": kode, "n": nama, "p": peran, "o": json.dumps(opd_ids or [])},
            )

    async def tambah(self, user: User) -> None:
        async with self._eng().begin() as c:
            await self._simpan_user(c, user)

    @staticmethod
    async def _simpan_user(conn, user: User) -> None:
        ada = (await conn.execute(
            text("SELECT 1 FROM bot_users WHERE telegram_id = :t"), {"t": user.telegram_id}
        )).first()
        params = {
            "t": user.telegram_id, "n": user.nama, "pr": user.peran,
            "o": json.dumps(user.opd_ids),
        }
        if ada:
            await conn.execute(
                text("UPDATE bot_users SET nama = :n, peran = :pr, opd_ids = :o "
                     "WHERE telegram_id = :t"), params,
            )
        else:
            await conn.execute(
                text("INSERT INTO bot_users (telegram_id, nama, peran, opd_ids, dibuat_pada) "
                     "VALUES (:t, :n, :pr, :o, :d)"), {**params, "d": _now()},
            )
