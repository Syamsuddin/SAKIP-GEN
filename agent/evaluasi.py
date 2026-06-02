"""Model hasil evaluasi internal (APIP/Inspektorat): temuan → rekomendasi → tindak lanjut.

Dibaca read-only dari skema sumber lewat profil (db/profiles/*.ambil_temuan). Berbeda
dari agent/evaluator.py (skoring LKE heuristik) — ini menampilkan temuan & status
tindak lanjut yang DICATAT di aplikasi SAKIP, bukan hasil hitungan agen.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class Rekomendasi(BaseModel):
    uraian: str
    prioritas: str | None = None        # RENDAH | SEDANG | TINGGI
    status: str | None = None           # status rekomendasi (BARU/DITINDAKLANJUTI/SELESAI/…)
    tindak_lanjut: str | None = None     # status tindak lanjut terakhir
    progres: float | None = None         # progres tindak lanjut (%)


class Temuan(BaseModel):
    uraian: str
    jenis: str | None = None             # KELEMAHAN | RISIKO | KETIDAKSESUAIAN | …
    tingkat_risiko: str | None = None    # RENDAH | SEDANG | TINGGI | KRITIS
    rekomendasi: list[Rekomendasi] = Field(default_factory=list)
