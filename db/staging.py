"""Lapisan tulis ke staging (ai_usulan) — satu-satunya tempat agen menulis.

Promosi dari staging ke tabel sumber dilakukan TERPISAH (aplikasi SAKIP / manusia
dengan kredensial berbeda). Stempel waktu disimpan sebagai string ISO-8601 UTC agar
portabel lintas SQLite (uji) dan MySQL (produksi).

INVARIAN STATUS (T4.2): kolom denormalisasi (`opd_id`, `tahun`, `indikator_id`,
`estimasi_poin`, `status`, dst.) adalah PROJECTION untuk query cepat. `payload` (JSON)
memegang state kanonik usulan KECUALI siklus hidup: **`status` selalu dibaca dari KOLOM**
(otoritatif), bukan dari payload. `putuskan_usulan` menyinkronkan keduanya saat menyimpan.
Definisi kolom kanonik tabel `ai_*` ada di db/schema.py (Core MetaData).
"""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import bindparam, text

import metrics
from agent.usulan import PerubahanField, UsulanPerbaikan
from db.engines import get_staging_engine

STAGING_SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS ai_usulan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipe TEXT NOT NULL,
    instansi TEXT,
    opd_id INTEGER NOT NULL,
    level TEXT,
    unit TEXT,
    indikator_id TEXT,
    tahun INTEGER,
    payload TEXT NOT NULL,
    gap_lke TEXT,
    estimasi_poin REAL,
    hash_data_lama TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    disusun_oleh TEXT,
    ditinjau_oleh TEXT,
    dibuat_pada TEXT,
    diputuskan_pada TEXT,
    diterapkan_oleh TEXT,
    diterapkan_pada TEXT
);
"""

_INSERT = text(
    """
    INSERT INTO ai_usulan
      (tipe, instansi, opd_id, level, unit, indikator_id, tahun, payload,
       gap_lke, estimasi_poin, hash_data_lama, status, disusun_oleh, dibuat_pada)
    VALUES
      (:tipe, :instansi, :opd_id, :level, :unit, :indikator_id, :tahun, :payload,
       :gap_lke, :estimasi_poin, :hash_data_lama, :status, :disusun_oleh, :dibuat_pada)
    """
)

_SELECT = text("SELECT * FROM ai_usulan WHERE id = :id")

_UPDATE = text(
    """
    UPDATE ai_usulan
    SET status = :status, ditinjau_oleh = :ditinjau_oleh,
        diputuskan_pada = :diputuskan_pada, payload = :payload
    WHERE id = :id
    """
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


async def simpan_draft(u: UsulanPerbaikan) -> int:
    """Simpan usulan sebagai draft; kembalikan id baris."""
    params = {
        "tipe": u.tipe, "instansi": u.instansi, "opd_id": u.opd_id,
        "level": u.level, "unit": u.unit, "indikator_id": u.indikator_id,
        "tahun": u.tahun, "payload": u.model_dump_json(),
        "gap_lke": u.gap_lke, "estimasi_poin": u.estimasi_poin,
        "hash_data_lama": u.hash_data_lama, "status": "draft",
        "disusun_oleh": u.disusun_oleh, "dibuat_pada": _now(),
    }
    async with get_staging_engine().begin() as conn:
        result = await conn.execute(_INSERT, params)
        metrics.inc("sakipgen_usulan_total")
        return int(result.lastrowid)


_UPDATE_PAYLOAD = text(
    "UPDATE ai_usulan SET payload = :payload WHERE id = :id AND status = 'draft'"
)


async def perbarui_draft(usulan_id: int, u: UsulanPerbaikan) -> bool:
    """Perbarui payload sebuah draft (mis. hasil penghalusan LLM latar). Status tetap 'draft'."""
    async with get_staging_engine().begin() as conn:
        res = await conn.execute(_UPDATE_PAYLOAD, {"id": usulan_id, "payload": u.model_dump_json()})
    return (res.rowcount or 0) > 0


async def ambil_usulan(usulan_id: int) -> UsulanPerbaikan | None:
    async with get_staging_engine().connect() as conn:
        row = (await conn.execute(_SELECT, {"id": usulan_id})).mappings().first()
    if row is None:
        return None
    u = UsulanPerbaikan.model_validate_json(row["payload"])
    u.id = int(row["id"])
    u.status = row["status"]
    u.ditinjau_oleh = row["ditinjau_oleh"]
    u.diterapkan_oleh = row.get("diterapkan_oleh")
    u.diterapkan_pada = row.get("diterapkan_pada")
    return u


async def putuskan_usulan(
    usulan_id: int,
    ditinjau_oleh: str,
    status: str,
    perubahan: list | None = None,
    alasan: str | None = None,
) -> bool:
    """Setujui/tolak usulan; opsional perbarui perubahan/alasan hasil suntingan form."""
    async with get_staging_engine().begin() as conn:
        row = (await conn.execute(_SELECT, {"id": usulan_id})).mappings().first()
        if row is None:
            return False
        u = UsulanPerbaikan.model_validate_json(row["payload"])
        if perubahan is not None:
            u.perubahan = [
                p if isinstance(p, PerubahanField) else PerubahanField(**p) for p in perubahan
            ]
        if alasan is not None:
            u.alasan = alasan
        u.status = status
        u.ditinjau_oleh = ditinjau_oleh
        await conn.execute(_UPDATE, {
            "id": usulan_id, "status": status, "ditinjau_oleh": ditinjau_oleh,
            "diputuskan_pada": _now(), "payload": u.model_dump_json(),
        })
    return True


async def daftar_usulan(
    opd_ids: list[int], status: str | None = None, limit: int = 10
) -> list[UsulanPerbaikan]:
    """Daftar usulan untuk sejumlah OPD (opsional difilter status), terbaru dulu."""
    if not opd_ids:
        return []
    sql = "SELECT * FROM ai_usulan WHERE opd_id IN :opds"
    params: dict = {"opds": list(opd_ids), "lim": limit}
    if status:
        sql += " AND status = :st"
        params["st"] = status
    sql += " ORDER BY id DESC LIMIT :lim"
    stmt = text(sql).bindparams(bindparam("opds", expanding=True))
    async with get_staging_engine().connect() as conn:
        rows = (await conn.execute(stmt, params)).mappings().all()
    hasil: list[UsulanPerbaikan] = []
    for r in rows:
        u = UsulanPerbaikan.model_validate_json(r["payload"])
        u.id = int(r["id"])
        u.status = r["status"]
        u.ditinjau_oleh = r["ditinjau_oleh"]
        hasil.append(u)
    return hasil
