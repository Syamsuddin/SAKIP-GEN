"""Uji Fase 2 — validitas nilai: komponen Hasil (capaian aktual), bobot terkalibrasi,
dan pengaman anti-gaming (peringatan integritas)."""
from __future__ import annotations

from datetime import UTC, datetime

from agent.dosir import (
    Capaian,
    DosirKinerja,
    Indikator,
    Meta,
    Pengukuran,
    Perencanaan,
    SasaranStrategis,
)
from agent.evaluator import evaluasi_lke


def _dosir(indikator: list[Indikator], capaian: list[Capaian]) -> DosirKinerja:
    return DosirKinerja(
        meta=Meta(instansi="Uji", opd_id=1, tahun=2026, dibuat_pada=datetime.now(UTC)),
        perencanaan=Perencanaan(sasaran_strategis=[
            SasaranStrategis(kode="1", uraian="S", indikator=indikator)]),
        pengukuran=Pengukuran(capaian=capaian),
    )


def _skor(hasil, nama):
    return next(k.skor for k in hasil.komponen if k.nama == nama)


def test_capaian_aktual_mempengaruhi_nilai():
    """Capaian tinggi vs rendah (data sama-sama lengkap) → nilai berbeda (T2.1/T2.2)."""
    ind = [Indikator(indikator_id="A", uraian="x", tipologi="outcome"),
           Indikator(indikator_id="B", uraian="y", tipologi="outcome")]
    tinggi = _dosir(ind, [
        Capaian(indikator_id="A", target=100, realisasi=100, persen_capaian=100.0),
        Capaian(indikator_id="B", target=100, realisasi=100, persen_capaian=100.0),
    ])
    rendah = _dosir(ind, [
        Capaian(indikator_id="A", target=100, realisasi=10, persen_capaian=10.0),
        Capaian(indikator_id="B", target=100, realisasi=10, persen_capaian=10.0),
    ])
    ht, hr = evaluasi_lke(tinggi), evaluasi_lke(rendah)
    assert _skor(ht, "Capaian Kinerja") == 100.0
    assert _skor(hr, "Capaian Kinerja") == 10.0
    assert ht.nilai_total > hr.nilai_total


def test_data_lengkap_capaian_nol_tidak_penuh():
    """Regresi bug inti: data lengkap tapi realisasi 0% TIDAK boleh bernilai penuh.

    Pengukuran (kelengkapan) = 100, tetapi Capaian (hasil) = 0.
    """
    ind = [Indikator(indikator_id="A", uraian="x", tipologi="outcome")]
    dosir = _dosir(ind, [
        Capaian(indikator_id="A", target=100, realisasi=0, persen_capaian=0.0),
    ])
    hasil = evaluasi_lke(dosir)
    assert _skor(hasil, "Pengukuran Kinerja") == 100.0   # data lengkap
    assert _skor(hasil, "Capaian Kinerja") == 0.0        # tapi tak tercapai
    assert hasil.nilai_total < 100.0


def test_capaian_di_cap_seratus():
    """Realisasi melebihi target tidak menggelembungkan skor (cap 100%)."""
    ind = [Indikator(indikator_id="A", uraian="x", tipologi="outcome")]
    dosir = _dosir(ind, [
        Capaian(indikator_id="A", target=100, realisasi=300, persen_capaian=300.0),
    ])
    assert _skor(evaluasi_lke(dosir), "Capaian Kinerja") == 100.0


def test_peringatan_mislabel_outcome():
    """T2.4 — indikator berlabel outcome tetapi rumusan berbau output → peringatan."""
    mislabel = _dosir(
        [Indikator(indikator_id="A", uraian="Jumlah sekolah terakreditasi", tipologi="outcome")],
        [],
    )
    h = evaluasi_lke(mislabel)
    assert h.peringatan and any("A" in p for p in h.peringatan)

    bersih = _dosir(
        [Indikator(indikator_id="B", uraian="Persentase sekolah terakreditasi", tipologi="outcome")],
        [],
    )
    assert evaluasi_lke(bersih).peringatan == []


def test_bobot_terkalibrasi():
    """T2.3 — bobot dapat dikalibrasi; nilai total mengikuti bobot yang diberikan."""
    ind = [Indikator(indikator_id="A", uraian="x", tipologi="outcome")]
    dosir = _dosir(ind, [
        Capaian(indikator_id="A", target=100, realisasi=50, persen_capaian=50.0),
    ])
    # Hanya komponen Capaian yang dibobot (100) → nilai_total == skor Capaian (50).
    hasil = evaluasi_lke(dosir, bobot={"Capaian Kinerja": 100.0})
    assert _skor(hasil, "Capaian Kinerja") == 50.0
    assert hasil.nilai_total == 50.0
