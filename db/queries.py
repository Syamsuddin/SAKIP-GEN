# SPDX-License-Identifier: MIT
# SAKIP-Gen — Evaluator + Drafter untuk SAKIP PermenPAN-RB 88/2021
# Lihat LICENSE untuk detail MIT License.

"""Jalur baca (read-only) → Dosir Kinerja, didelegasikan ke profil skema aktif.

Logika domain tak mengenal nama tabel/kolom fisik; pemetaan skema spesifik (eSAKIP,
referensi, dll) berada di db/profiles/*. Profil dipilih lewat DB_SCHEMA_PROFILE.
Lihat db/profiles/base.py untuk kontraknya.
"""
from __future__ import annotations

from agent.dosir import DosirKinerja
from db.profiles import get_profile


async def bangun_dosir(opd_id: int, tahun: int) -> DosirKinerja:
    """Susun Dosir Kinerja lengkap satu OPD dari sumber (read-only) via profil aktif."""
    return await get_profile().bangun_dosir(opd_id, tahun)


async def resolve_opd_id(ref: str) -> int | None:
    """Terjemahkan referensi OPD (ID numerik atau kode) menjadi id, bila ada."""
    return await get_profile().resolve_opd_id(ref)


async def daftar_opd() -> list[dict]:
    """Daftar seluruh OPD (untuk penjadwal push)."""
    return await get_profile().daftar_opd()
