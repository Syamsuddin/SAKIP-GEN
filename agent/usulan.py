"""Model usulan perbaikan (Fase 3) — objek terstruktur yang dirender satu template.

UsulanPerbaikan adalah objek netral: satu indikator + daftar perubahan field
(lama -> usulan) + alasan + jejak (gap, estimasi, hash data lama untuk optimistic
lock). Disimpan ke staging; promosi ke tabel sumber dilakukan terpisah oleh manusia.
"""
from __future__ import annotations

import hashlib
import json

from pydantic import BaseModel, Field

from agent.dosir import Indikator


class PerubahanField(BaseModel):
    field: str
    lama: str | None = None
    usulan: str | None = None


class UsulanPerbaikan(BaseModel):
    id: int | None = None
    tipe: str = "perbaikan_indikator"
    instansi: str
    opd_id: int
    level: str = "dinas"            # dinas | bidang | seksi
    unit: str | None = None
    indikator_id: str
    tahun: int
    perubahan: list[PerubahanField] = Field(default_factory=list)
    alasan: str = ""
    gap_lke: str | None = None
    estimasi_poin: float = 0.0
    hash_data_lama: str
    status: str = "draft"          # draft | disetujui | ditolak | diterapkan
    disusun_oleh: str = "agen"
    ditinjau_oleh: str | None = None
    diterapkan_oleh: str | None = None
    diterapkan_pada: str | None = None


def hash_indikator(ind: Indikator) -> str:
    """Sidik jari data indikator saat usulan dibuat (untuk deteksi data basi)."""
    payload = json.dumps(
        {
            "indikator_id": ind.indikator_id,
            "uraian": ind.uraian,
            "satuan": ind.satuan,
            "tipologi": ind.tipologi,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
