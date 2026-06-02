"""Event log (Fase 5): jejak aktivitas & keamanan, dwi-sink (logger + DB best-effort).

ai_event mencatat SIAPA melakukan APA, KAPAN, dan HASILNYA — terlepas dari Telegram
(Telegram hanya pemicu, bukan system of record). Selalu tercatat ke logger; insert DB
dilewati dengan peringatan bila engine staging belum siap. Berbeda dari ai_audit
(Fase 4) yang khusus mencatat perubahan data sumber (sebelum/sesudah).
"""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from sqlalchemy import text

from config import get_settings
from db.engines import get_staging_engine

logger = logging.getLogger("sakip-gen.audit")

EVENT_SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS ai_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pada TEXT NOT NULL,
    kategori TEXT NOT NULL,
    aksi TEXT NOT NULL,
    telegram_id INTEGER,
    nama TEXT,
    peran TEXT,
    opd_id INTEGER,
    status TEXT,
    ringkas TEXT,
    request_id TEXT,
    detail TEXT
);
"""

_INSERT = text(
    """
    INSERT INTO ai_event
      (pada, kategori, aksi, telegram_id, nama, peran, opd_id, status, ringkas, request_id, detail)
    VALUES
      (:pada, :kategori, :aksi, :telegram_id, :nama, :peran, :opd_id, :status, :ringkas, :request_id, :detail)
    """
)


async def catat(
    kategori: str,
    aksi: str,
    *,
    telegram_id: int | None = None,
    nama: str | None = None,
    peran: str | None = None,
    opd_id: int | None = None,
    status: str = "ok",
    ringkas: str | None = None,
    request_id: str | None = None,
    detail: dict | None = None,
) -> None:
    """Catat satu peristiwa. Tidak pernah melempar error (best-effort)."""
    rec = {
        "pada": datetime.now(UTC).isoformat(),
        "kategori": kategori, "aksi": aksi, "telegram_id": telegram_id,
        "nama": nama, "peran": peran, "opd_id": opd_id, "status": status,
        "ringkas": ringkas, "request_id": request_id,
        "detail": json.dumps(detail, ensure_ascii=False) if detail is not None else None,
    }
    # Sink 1: logger (selalu).
    logger.info("AUDIT %s", json.dumps({k: v for k, v in rec.items() if v is not None}, ensure_ascii=False))

    # Sink 2: DB (best-effort).
    try:
        aktif = get_settings().audit_to_db
    except Exception:  # noqa: BLE001 — settings belum siap
        aktif = True
    if not aktif:
        return
    try:
        engine = get_staging_engine()
    except Exception:  # noqa: BLE001 — engine staging belum dikonfigurasi
        logger.debug("Audit DB dilewati: engine staging belum siap.")
        return
    try:
        async with engine.begin() as conn:
            await conn.execute(_INSERT, rec)
    except Exception as e:  # noqa: BLE001
        logger.warning("Gagal menulis audit ke DB: %s", e)


async def ambil_peristiwa(limit: int = 50) -> list[dict]:
    """Ambil peristiwa terbaru (inspeksi/uji)."""
    async with get_staging_engine().connect() as conn:
        rows = (await conn.execute(
            text("SELECT * FROM ai_event ORDER BY id DESC LIMIT :n"), {"n": limit}
        )).mappings().all()
    return [dict(r) for r in rows]
