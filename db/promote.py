"""Penerapan usulan yang DISETUJUI ke tabel sumber (Fase 4) — bagian paling sensitif.

Pengaman berlapis:
1. Hanya usulan berstatus 'disetujui' yang dapat diterapkan.
2. Optimistic lock: data sumber saat ini di-hash ulang dan dibandingkan dengan
   hash_data_lama pada usulan; bila berbeda, penerapan DITOLAK (data telah berubah).
3. Whitelist kolom: hanya field yang diizinkan PROFIL aktif yang boleh diubah —
   selaras dengan GRANT kolom kredensial promotor.
4. Transaksional + audit: perubahan, status, dan jejak (sebelum/sesudah) ditulis
   dalam satu transaksi. Promosi ini DIPICU MANUSIA (bukan oleh agen).

Akses kolom sumber (baca + tulis) didelegasikan ke profil skema aktif (db/profiles/*),
sehingga logika pengaman ini netral terhadap skema eSAKIP yang dipakai.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import text

from agent.usulan import UsulanPerbaikan, hash_indikator
from db.engines import get_promote_engine
from db.profiles import get_profile

AUDIT_SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS ai_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usulan_id INTEGER,
    aksi TEXT NOT NULL,
    tabel_sasaran TEXT NOT NULL,
    kunci TEXT NOT NULL,
    data_sebelum TEXT,
    data_sesudah TEXT,
    oleh TEXT NOT NULL,
    pada TEXT NOT NULL
);
"""


@dataclass
class HasilPenerapan:
    ok: bool
    pesan: str
    usulan_id: int
    sebelum: dict | None = None
    sesudah: dict | None = None
    field_diterapkan: list[str] = field(default_factory=list)
    field_diabaikan: list[str] = field(default_factory=list)


_SQL_USULAN = text("SELECT id, status, payload FROM ai_usulan WHERE id = :id")

_SQL_AUDIT = text(
    """
    INSERT INTO ai_audit
      (usulan_id, aksi, tabel_sasaran, kunci, data_sebelum, data_sesudah, oleh, pada)
    VALUES
      (:usulan_id, :aksi, :tabel, :kunci, :sebelum, :sesudah, :oleh, :pada)
    """
)

_SQL_TANDAI = text(
    """
    UPDATE ai_usulan
    SET status = 'diterapkan', diterapkan_oleh = :oleh, diterapkan_pada = :pada
    WHERE id = :id
    """
)


async def terapkan_usulan(usulan_id: int, oleh: str) -> HasilPenerapan:
    """Terapkan satu usulan 'disetujui' ke tabel sumber, dengan audit. Idempoten-aman."""
    profile = get_profile()
    eng = get_promote_engine()
    async with eng.begin() as conn:
        row = (await conn.execute(_SQL_USULAN, {"id": usulan_id})).mappings().first()
        if row is None:
            return HasilPenerapan(False, "Usulan tidak ditemukan.", usulan_id)
        if row["status"] != "disetujui":
            return HasilPenerapan(
                False,
                f"Status usulan '{row['status']}'. Hanya 'disetujui' yang dapat diterapkan.",
                usulan_id,
            )
        u = UsulanPerbaikan.model_validate_json(row["payload"])
        if u.tipe != "perbaikan_indikator":
            return HasilPenerapan(
                False, f"Tipe usulan '{u.tipe}' belum didukung penerapan otomatis.", usulan_id
            )

        ind_kini = await profile.baca_indikator(
            conn, indikator_id=u.indikator_id, opd_id=u.opd_id, tahun=u.tahun
        )
        if ind_kini is None:
            return HasilPenerapan(
                False, "Indikator sumber tidak ditemukan (kode/OPD/tahun tidak cocok).", usulan_id
            )

        if hash_indikator(ind_kini) != u.hash_data_lama:
            return HasilPenerapan(
                False, "Data sumber telah berubah sejak usulan dibuat; tinjau & susun ulang.",
                usulan_id,
            )

        sebelum = {"uraian": ind_kini.uraian, "satuan": ind_kini.satuan,
                   "tipologi": ind_kini.tipologi}
        sesudah = dict(sebelum)
        diterapkan, diabaikan = [], []
        for p in u.perubahan:
            if p.field in profile.kolom_diizinkan:
                sesudah[p.field] = p.usulan
                diterapkan.append(p.field)
            else:
                diabaikan.append(p.field)
        if not diterapkan:
            return HasilPenerapan(
                False, "Tidak ada field yang dapat diterapkan (di luar whitelist).",
                usulan_id, sebelum=sebelum, field_diabaikan=diabaikan,
            )

        now = datetime.now(UTC).isoformat()
        await profile.terapkan_indikator(
            conn, indikator_id=u.indikator_id, opd_id=u.opd_id, tahun=u.tahun,
            nilai={f: sesudah[f] for f in diterapkan},
        )
        await conn.execute(_SQL_AUDIT, {
            "usulan_id": usulan_id, "aksi": "terapkan", "tabel": "indikator",
            "kunci": f"id={u.indikator_id};opd={u.opd_id};tahun={u.tahun}",
            "sebelum": json.dumps(sebelum, ensure_ascii=False),
            "sesudah": json.dumps(sesudah, ensure_ascii=False),
            "oleh": oleh, "pada": now,
        })
        await conn.execute(_SQL_TANDAI, {"id": usulan_id, "oleh": oleh, "pada": now})

    return HasilPenerapan(
        True, "Usulan diterapkan ke tabel sumber.", usulan_id,
        sebelum=sebelum, sesudah=sesudah,
        field_diterapkan=diterapkan, field_diabaikan=diabaikan,
    )
