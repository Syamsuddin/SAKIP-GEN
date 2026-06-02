"""Uji Fase 5 — analitik lanjutan & skala: tren/delta, benchmark/peringkat,
keselarasan sasaran↔indikator, indikator berisiko, dan factory limiter."""
from __future__ import annotations

from datetime import UTC, datetime

from agent.analitik import (
    delta_nilai,
    indikator_berisiko,
    keselarasan_sasaran,
    peringkat,
)
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
            SasaranStrategis(kode="1", uraian="Sasaran 1", indikator=indikator)]),
        pengukuran=Pengukuran(capaian=capaian),
    )


# ---------- T5.2: delta antar-tahun ----------
def test_delta_nilai():
    ind = [Indikator(indikator_id="A", uraian="x", tipologi="outcome")]
    lalu = evaluasi_lke(_dosir(ind, [Capaian(indikator_id="A", target=100, realisasi=50,
                                             persen_capaian=50.0)]))
    kini = evaluasi_lke(_dosir(ind, [Capaian(indikator_id="A", target=100, realisasi=90,
                                             persen_capaian=90.0)]))
    d = delta_nilai(kini, lalu)
    assert d["total"] > 0
    assert d["komponen"]["Capaian Kinerja"] == 40.0  # 90 − 50


# ---------- T5.2: peringkat benchmark ----------
def test_peringkat():
    r = peringkat([("A", 70.0), ("B", 80.0), ("C", 60.0)])
    assert r[0] == (1, "B", 80.0)
    assert r[1] == (2, "A", 70.0)
    assert r[2] == (3, "C", 60.0)


# ---------- T5.3: keselarasan sasaran↔indikator ----------
def test_keselarasan_sasaran():
    hanya_output = _dosir([Indikator(indikator_id="A", uraian="Jumlah x", tipologi="output")], [])
    assert keselarasan_sasaran(hanya_output)  # tak ada outcome → ditandai

    ada_outcome = _dosir([Indikator(indikator_id="B", uraian="Persentase y", tipologi="outcome")], [])
    assert keselarasan_sasaran(ada_outcome) == []


# ---------- T5.4: indikator berisiko ----------
def test_indikator_berisiko():
    rendah = _dosir([Indikator(indikator_id="A", uraian="x", tipologi="output")],
                    [Capaian(indikator_id="A", target=100, realisasi=40, persen_capaian=40.0)])
    r = indikator_berisiko(rendah, ambang=75.0)
    assert any("A" in x and "40%" in x for x in r)

    aman = _dosir([Indikator(indikator_id="A", uraian="x", tipologi="output")],
                  [Capaian(indikator_id="A", target=100, realisasi=90, persen_capaian=90.0)])
    assert indikator_berisiko(aman, ambang=75.0) == []


# ---------- T5.4/T5.3: bagian peringatan dini push triwulanan ----------
def test_bagian_dini_push():
    from bot.scheduler import _bagian_dini

    dosir = _dosir([Indikator(indikator_id="A", uraian="Jumlah dokumen", tipologi="output")],
                   [Capaian(indikator_id="A", target=100, realisasi=40, persen_capaian=40.0)])
    txt = _bagian_dini(dosir)
    assert "berisiko" in txt        # capaian 40% < 75%
    assert "Keselarasan" in txt     # sasaran tanpa indikator outcome


# ---------- T5.1: factory limiter (default in-memory) ----------
def test_buat_limiter_default():
    from config import Settings
    from web.ratelimit import SlidingWindowLimiter, buat_limiter

    s = Settings(bot_token="x", webhook_secret="x" * 16, public_base_url="https://x",
                 _env_file=None)  # tanpa REDIS_URL
    lim = buat_limiter(limit=2, window=60.0, settings=s)
    assert isinstance(lim, SlidingWindowLimiter)


async def test_limiter_cek_async():
    from web.ratelimit import SlidingWindowLimiter

    lim = SlidingWindowLimiter(limit=2, window=60.0)
    assert (await lim.cek_async("k"))[0] is True
    assert (await lim.cek_async("k"))[0] is True
    ok, retry = await lim.cek_async("k")
    assert ok is False and retry > 0
