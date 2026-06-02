# SPDX-License-Identifier: MIT
# SAKIP-Gen — Evaluator + Drafter untuk SAKIP PermenPAN-RB 88/2021
# Lihat LICENSE untuk detail MIT License.

"""Orkestrasi tingkat tinggi Fase 1: baca data -> susun Dosir -> evaluasi."""
from __future__ import annotations

import metrics
from agent.dokumen import Dokumen
from agent.dosir import Capaian, DosirKinerja
from agent.evaluasi import Temuan
from agent.evaluator import HasilEvaluasi, evaluasi_lke
from agent.keselarasan import RelasiKinerja
from db.profiles import get_profile
from db.queries import bangun_dosir


async def evaluasi_opd(opd_id: int, tahun: int) -> tuple[DosirKinerja, HasilEvaluasi]:
    """Susun Dosir Kinerja satu OPD dari MySQL (RO) lalu nilai dengan LKE."""
    dosir = await bangun_dosir(opd_id, tahun)
    metrics.inc("sakipgen_evaluasi_total")
    return dosir, evaluasi_lke(dosir)


async def temuan_opd(opd_id: int, tahun: int) -> list[Temuan]:
    """Temuan evaluasi internal + rekomendasi + status tindak lanjut (read-only via profil)."""
    return await get_profile().ambil_temuan(opd_id, tahun)


async def capaian_periode(opd_id: int, tahun: int, periode: str) -> list[Capaian]:
    """Capaian per periode (tw1..tw4/smt) via profil. [] bila periode tak punya data."""
    return await get_profile().ambil_capaian(opd_id, tahun, periode)


async def dokumen_opd(
    opd_id: int, tahun: int | None = None, jenis: str | None = None
) -> list[Dokumen]:
    """Telusur dokumen SAKIP OPD (+ versi & bukti) via profil. [] bila tak ada/tak didukung."""
    return await get_profile().ambil_dokumen(opd_id, tahun, jenis)


async def cascading_opd(opd_id: int, tahun: int) -> list[RelasiKinerja]:
    """Relasi cascading/keselarasan pohon kinerja OPD via profil. [] bila tak ada/tak didukung."""
    return await get_profile().ambil_cascading(opd_id, tahun)
