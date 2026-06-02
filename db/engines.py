# SPDX-License-Identifier: MIT
# SAKIP-Gen — Evaluator + Drafter untuk SAKIP PermenPAN-RB 88/2021
# Lihat LICENSE untuk detail MIT License.

"""Engine SQLAlchemy: read-only (analitik) dan staging (usulan).

Pemisahan MODE diwujudkan lewat kredensial terpisah, bukan flag konfigurasi.
Engine dibuat malas (lazy) agar Fase 0/1 berjalan & dapat diuji tanpa MySQL,
serta dapat di-override untuk pengujian (mis. dengan SQLite).
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from config import get_settings

_ro_engine: AsyncEngine | None = None
_staging_engine: AsyncEngine | None = None


def get_ro_engine() -> AsyncEngine:
    """Engine read-only untuk analitik. Memakai user MySQL ber-GRANT SELECT."""
    global _ro_engine
    if _ro_engine is None:
        url = get_settings().db_ro_url
        if not url:
            raise RuntimeError("DB_RO_URL belum diset di .env")
        _ro_engine = create_async_engine(url, pool_pre_ping=True, pool_recycle=1800)
    return _ro_engine


def get_staging_engine() -> AsyncEngine:
    """Engine untuk menulis usulan ke skema staging (dipakai Fase 3)."""
    global _staging_engine
    if _staging_engine is None:
        url = get_settings().db_staging_url
        if not url:
            raise RuntimeError("DB_STAGING_URL belum diset di .env")
        _staging_engine = create_async_engine(url, pool_pre_ping=True, pool_recycle=1800)
    return _staging_engine


def set_ro_engine(engine: AsyncEngine) -> None:
    """Override engine read-only (dipakai pengujian)."""
    global _ro_engine
    _ro_engine = engine


def set_staging_engine(engine: AsyncEngine) -> None:
    global _staging_engine
    _staging_engine = engine


_promote_engine: AsyncEngine | None = None


def get_promote_engine() -> AsyncEngine:
    """Engine PROMOTOR (Fase 4): hak tulis paling sempit ke tabel sumber.

    Memakai kredensial terpisah dengan GRANT level kolom (mis.
    UPDATE(uraian,satuan,tipologi) pada `indikator`). Dipakai HANYA untuk
    menerapkan usulan yang sudah berstatus 'disetujui'.
    """
    global _promote_engine
    if _promote_engine is None:
        url = get_settings().db_promote_url
        if not url:
            raise RuntimeError("DB_PROMOTE_URL belum diset di .env")
        _promote_engine = create_async_engine(url, pool_pre_ping=True, pool_recycle=1800)
    return _promote_engine


def set_promote_engine(engine: AsyncEngine) -> None:
    global _promote_engine
    _promote_engine = engine
