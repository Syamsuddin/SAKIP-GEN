"""Pemeriksaan kesiapan (readiness) — dipakai endpoint /readyz (Fase 7)."""
from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import text


async def readiness(getters: list[tuple[str, Callable]]) -> tuple[bool, dict]:
    """Cek tiap engine. 'not-configured' tidak menggagalkan; 'fail' menggagalkan."""
    checks: dict[str, str] = {}
    overall = True
    for nama, getter in getters:
        try:
            engine = getter()
        except Exception:  # noqa: BLE001 — engine belum dikonfigurasi
            checks[nama] = "not-configured"
            continue
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks[nama] = "ok"
        except Exception:  # noqa: BLE001
            checks[nama] = "fail"
            overall = False
    return overall, checks
