"""Uji penerjemah bahasa alami → Intent (agent/nlu) — heuristik deterministik."""
from __future__ import annotations

import agent.nlu as nlu
from agent.nlu import cocokkan_opd, parse


def test_parse_evaluasi():
    i = parse("tolong nilai kinerja OPD 1 tahun 2026")
    assert i is not None and i.aksi == "evaluasi" and i.opd_ref == "1" and i.tahun == 2026


def test_parse_gap():
    i = parse("apa kelemahan opd 2")
    assert i is not None and i.aksi == "gap" and i.opd_ref == "2"


def test_parse_usul():
    assert parse("buatkan usulan perbaikan opd 1").aksi == "usul"


def test_parse_usulan_list():
    assert parse("lihat daftar usulan opd 1").aksi == "usulan"


def test_parse_tren_bukan_benchmark():
    # "dibanding tahun lalu" = tren, JANGAN tertukar dengan benchmark.
    i = parse("bagaimana perkembangan nilai opd 1 dibanding tahun lalu")
    assert i is not None and i.aksi == "tren" and i.opd_ref == "1"


def test_parse_benchmark_tanpa_opd():
    i = parse("bandingkan OPD tahun 2026")
    assert i is not None and i.aksi == "benchmark" and i.opd_ref is None and i.tahun == 2026


def test_parse_status():
    assert parse("status saya apa peran nya").aksi == "status"


def test_parse_bantuan():
    assert parse("bisa apa saja sih").aksi == "bantuan"


def test_parse_kode_kapital():
    i = parse("nilai DIKBUD")
    assert i is not None and i.aksi == "evaluasi" and i.opd_ref == "DIKBUD"


def test_parse_daftar_opd():
    assert parse("OPD apa saja yang ada di database saat ini?").aksi == "daftar_opd"
    assert parse("daftar opd").aksi == "daftar_opd"
    assert parse("ada opd apa saja").aksi == "daftar_opd"


def test_apa_saja_tidak_membajak_aksi():
    # "apa saja" TIDAK boleh menutupi aksi nyata (bantuan kini fallback terakhir).
    assert parse("apa saja usul perbaikan OPD 1").aksi == "usul"
    assert parse("kelemahan apa saja di opd 1").aksi == "gap"
    # "apa saja" murni → bantuan.
    assert parse("bisa apa saja sih").aksi == "bantuan"


def test_parse_tidak_paham():
    assert parse("halo selamat pagi") is None
    assert parse("") is None


def test_cocokkan_opd():
    daftar = [
        {"id": 1, "kode": "DIKBUD", "nama": "Dinas Pendidikan Kabupaten Seruyan"},
        {"id": 2, "kode": "DINKES", "nama": "Dinas Kesehatan Kabupaten Seruyan"},
    ]
    assert cocokkan_opd("1", daftar) == 1            # id
    assert cocokkan_opd("DIKBUD", daftar) == 1       # kode
    assert cocokkan_opd("dikbud", daftar) == 1       # kode case-insensitive
    assert cocokkan_opd("dinas kesehatan", daftar) == 2  # nama
    assert cocokkan_opd("9", daftar) is None         # id tak ada
    assert cocokkan_opd("dinas xyz", daftar) is None  # nama tak cocok
    assert cocokkan_opd(None, daftar) is None


async def test_parse_llm_fallback(monkeypatch):
    # Heuristik gagal → fallback LLM mengembalikan JSON terstruktur.
    import agent.llm as llm

    async def fake(prompt, *, system, settings=None):
        return '{"aksi":"evaluasi","opd":"3","tahun":2026}'

    monkeypatch.setattr(llm, "jawab_singkat", fake)
    i = await nlu.parse_llm("coba lihatkan performa instansi nomor tiga dong")
    assert i is not None and i.aksi == "evaluasi" and i.opd_ref == "3" and i.tahun == 2026
