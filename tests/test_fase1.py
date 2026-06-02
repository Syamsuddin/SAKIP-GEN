"""Uji Fase 1: model Dosir, evaluator, dan alur end-to-end via SQLite."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest_asyncio

from agent.dosir import (
    DosirKinerja,
    Indikator,
    Meta,
    Pengukuran,
    Perencanaan,
    SasaranStrategis,
)
from agent.evaluator import evaluasi_lke, predikat_dari_nilai
from agent.service import evaluasi_opd
from db.engines import set_ro_engine
from demo_evaluasi import build_demo_engine

PREDIKAT_VALID = {"AA", "A", "BB", "B", "CC", "C", "D"}


@pytest_asyncio.fixture
async def demo_engine():
    eng = await build_demo_engine()
    set_ro_engine(eng)
    yield eng
    await eng.dispose()


def test_predikat_thresholds():
    assert predikat_dari_nilai(95)[0] == "AA"
    assert predikat_dari_nilai(85)[0] == "A"
    assert predikat_dari_nilai(75)[0] == "BB"
    assert predikat_dari_nilai(65)[0] == "B"
    assert predikat_dari_nilai(20)[0] == "D"


def test_evaluator_synthetic_tanpa_capaian():
    dosir = DosirKinerja(
        meta=Meta(instansi="Uji", opd_id=9, tahun=2026, dibuat_pada=datetime.now(UTC)),
        perencanaan=Perencanaan(sasaran_strategis=[
            SasaranStrategis(kode="1", uraian="S", indikator=[
                Indikator(indikator_id="A", uraian="x", tipologi="output"),
            ])
        ]),
        pengukuran=Pengukuran(capaian=[]),
    )
    hasil = evaluasi_lke(dosir)
    assert hasil.predikat in PREDIKAT_VALID
    # tanpa capaian -> ada gap pengukuran; indikator output -> ada gap perencanaan
    komp_gap = {g.komponen for g in hasil.gap}
    assert "Pengukuran Kinerja" in komp_gap
    assert "Perencanaan Kinerja" in komp_gap


async def test_end_to_end_via_sqlite(demo_engine):
    dosir, hasil = await evaluasi_opd(opd_id=1, tahun=2026)
    # Dosir tersusun dari DB
    assert dosir.meta.instansi == "Dinas Pendidikan Kabupaten Seruyan"
    assert len(dosir.perencanaan.sasaran_strategis) == 2
    assert sum(len(s.indikator) for s in dosir.perencanaan.sasaran_strategis) == 4
    # Hasil evaluasi konsisten
    assert hasil.predikat in PREDIKAT_VALID
    assert 0 <= hasil.nilai_total <= 100
    assert {k.nama for k in hasil.komponen} == {
        "Perencanaan Kinerja", "Pengukuran Kinerja",
        "Pelaporan Kinerja", "Evaluasi Akuntabilitas Kinerja Internal",
        "Capaian Kinerja",
    }
    # IKU-2.2 tanpa capaian -> gap pengukuran muncul
    assert any(g.komponen == "Pengukuran Kinerja" for g in hasil.gap)
    # gap terurut menurun berdasarkan estimasi poin
    poin = [g.estimasi_poin for g in hasil.gap]
    assert poin == sorted(poin, reverse=True)
