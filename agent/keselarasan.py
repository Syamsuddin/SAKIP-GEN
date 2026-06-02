"""Model keselarasan/cascading kinerja: relasi antar-node pohon kinerja.

Dibaca read-only dari `sakip_cascading_relasi` lewat profil (db/profiles/*.ambil_cascading).
Menunjukkan bagaimana sasaran OPD diturunkan dari kinerja atasan (Pemda) — `arah="naik"` —
atau diturunkan ke unit/eselon di bawahnya — `arah="turun"`. Dipakai /rencana dok=pohon.
"""
from __future__ import annotations

from pydantic import BaseModel


class RelasiKinerja(BaseModel):
    parent: str                          # uraian node induk
    child: str                           # uraian node anak
    jenis: str                           # TURUNAN_LANGSUNG | KONTRIBUSI | DUKUNGAN | …
    bobot: float | None = None           # bobot kontribusi (%) bila ada
    arah: str                            # "naik" (OPD→atasan) | "turun" (OPD→unit)
