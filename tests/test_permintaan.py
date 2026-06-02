"""Uji tata bahasa terpadu Permintaan + ekstraksi slot baru oleh NLU."""
from __future__ import annotations

from agent import nlu
from agent.permintaan import (
    AKSI_VALID,
    Permintaan,
    kanonik_dokumen,
    kanonik_periode,
)


def test_alias_intent_permintaan():
    assert nlu.Intent is Permintaan
    p = Permintaan(aksi="nilai")
    assert p.skor == 1.0 and p.opd_ref is None


def test_kanonik_periode():
    assert kanonik_periode("triwulan 2") == "tw2"
    assert kanonik_periode("TW3") == "tw3"
    assert kanonik_periode("semester 1") == "smt1"
    assert kanonik_periode("ngawur") is None


def test_kanonik_dokumen():
    assert kanonik_dokumen("perjanjian kinerja") == "pk"
    assert kanonik_dokumen("pohon kinerja") == "pohon"
    assert kanonik_dokumen("LKIP") == "lkjip"
    assert kanonik_dokumen("xx") is None


def test_butuh_opd():
    assert Permintaan(aksi="nilai").butuh_opd() is False  # 'nilai' bukan aksi internal NLU
    assert Permintaan(aksi="evaluasi").butuh_opd() is True
    assert Permintaan(aksi="benchmark").butuh_opd() is False
    assert Permintaan(aksi="rencana").butuh_opd() is True


# ---------- Ekstraksi slot oleh nlu.parse ----------
def test_parse_capaian_dengan_periode():
    p = nlu.parse("capaian opd 1 triwulan 2 2026")
    assert p.aksi == "capaian" and p.opd_ref == "1" and p.periode == "tw2" and p.tahun == 2026


def test_parse_rencana_dokumen():
    p = nlu.parse("lihat pohon kinerja dinas pendidikan")
    assert p.aksi == "rencana" and p.dokumen == "pohon"


def test_parse_laporan_lkjip():
    p = nlu.parse("buatkan draft analisis capaian untuk LKjIP opd 1")
    assert p.aksi == "laporan" and p.dokumen == "lkjip" and p.opd_ref == "1"


def test_parse_temuan():
    assert nlu.parse("lihat temuan & rekomendasi inspektorat opd 1").aksi == "temuan"


def test_parse_evaluasi_tetap():
    # Verba lama tetap berfungsi (kompatibilitas).
    p = nlu.parse("nilai kinerja opd 1 tahun 2026")
    assert p.aksi == "evaluasi" and p.opd_ref == "1" and p.tahun == 2026


def test_aksi_baru_di_himpunan():
    for a in ("rencana", "capaian", "laporan", "temuan", "dokumen"):
        assert a in AKSI_VALID
