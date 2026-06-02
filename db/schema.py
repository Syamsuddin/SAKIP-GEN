"""Definisi KANONIK tabel milik agen (SQLAlchemy Core MetaData) — Fase 4 (T4.1).

Satu sumber kebenaran untuk kolom tabel `ai_*` + auth. Dipakai oleh:
- Alembic (autogenerate migrasi `ai_*`) — `target_metadata = metadata` (T4.3).
- Pengujian: `buat_skema_agen(engine)` membangun skema di SQLite in-memory.
- Uji penjaga-drift memastikan definisi ini selaras dengan *_SCHEMA_SQLITE di modul.

Tabel SUMBER eSAKIP TIDAK didefinisikan di sini — itu milik aplikasi SAKIP dan
dipetakan adaptif lewat db/profiles/* (lihat db/mysql/schema.sql). Stempel waktu
disimpan sebagai string ISO-8601 (VARCHAR) agar portabel SQLite↔MySQL.
"""
from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Column,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
)
from sqlalchemy.ext.asyncio import AsyncEngine

metadata = MetaData()

ai_usulan = Table(
    "ai_usulan", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("tipe", String(64), nullable=False, server_default="perbaikan_indikator"),
    Column("instansi", String(255)),
    Column("opd_id", Integer, nullable=False),
    Column("level", String(16), server_default="dinas"),
    Column("unit", String(255)),
    Column("indikator_id", String(64)),
    Column("tahun", Integer, nullable=False),
    Column("payload", Text, nullable=False),
    Column("gap_lke", String(128)),
    Column("estimasi_poin", Float, nullable=False, server_default="0"),
    Column("hash_data_lama", String(64), nullable=False),
    Column("status", String(16), nullable=False, server_default="draft"),
    Column("disusun_oleh", String(64), server_default="agen"),
    Column("ditinjau_oleh", String(128)),
    Column("dibuat_pada", String(32)),
    Column("diputuskan_pada", String(32)),
    Column("diterapkan_oleh", String(128)),
    Column("diterapkan_pada", String(32)),
)

ai_audit = Table(
    "ai_audit", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("usulan_id", Integer),
    Column("aksi", String(32), nullable=False),
    Column("tabel_sasaran", String(64), nullable=False),
    Column("kunci", String(255), nullable=False),
    Column("data_sebelum", Text),
    Column("data_sesudah", Text),
    Column("oleh", String(128), nullable=False),
    Column("pada", String(32), nullable=False),
)

ai_event = Table(
    "ai_event", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("pada", String(32), nullable=False),
    Column("kategori", String(64), nullable=False),
    Column("aksi", String(64), nullable=False),
    Column("telegram_id", BigInteger),
    Column("nama", String(128)),
    Column("peran", String(32)),
    Column("opd_id", Integer),
    Column("status", String(32)),
    Column("ringkas", Text),
    Column("request_id", String(64)),
    Column("detail", Text),
)

bot_users = Table(
    "bot_users", metadata,
    Column("telegram_id", BigInteger, primary_key=True, autoincrement=False),
    Column("nama", String(128)),
    Column("peran", String(32), server_default="operator"),
    Column("opd_ids", Text),
    Column("dibuat_pada", String(32)),
)

registration_codes = Table(
    "registration_codes", metadata,
    Column("kode", String(64), primary_key=True),
    Column("nama", String(128)),
    Column("peran", String(32), server_default="operator"),
    Column("opd_ids", Text),
    Column("dipakai", Integer, server_default="0"),
    Column("dipakai_oleh", BigInteger),
    Column("dipakai_pada", String(32)),
)

# Subset tabel yang umum dibutuhkan jalur usulan (untuk helper uji).
TABEL_USULAN = (ai_usulan, ai_audit, ai_event)


async def buat_skema_agen(engine: AsyncEngine, *tabel: Table) -> None:
    """Bangun tabel milik agen pada engine (SQLite uji). Tanpa argumen → semua tabel."""
    daftar = list(tabel) or list(metadata.tables.values())
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: metadata.create_all(c, tables=daftar))
