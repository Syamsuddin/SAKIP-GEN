"""Uji Fase 3 — kematangan AI: caching respons, circuit breaker, prompt diperkaya,
deteksi mislabel LLM, dan saran lanjutan (advisory). Tanpa panggilan API nyata."""
from __future__ import annotations

import agent.llm as llm
from config import Settings


def _settings_anthropic():
    return Settings(bot_token="x", webhook_secret="x" * 16, public_base_url="https://x",
                    anthropic_api_key="key", _env_file=None)


# ---------- T3.2: caching respons ----------
async def test_rumuskan_outcome_caching(monkeypatch):
    panggilan = {"n": 0}

    async def fake(prompt, settings, system=None):
        panggilan["n"] += 1
        return "Persentase sekolah terakreditasi minimal B"

    monkeypatch.setattr(llm, "_via_anthropic", fake)
    s = _settings_anthropic()

    a = await llm.rumuskan_outcome("Jumlah sekolah terakreditasi", tipologi="output", settings=s)
    b = await llm.rumuskan_outcome("Jumlah sekolah terakreditasi", tipologi="output", settings=s)
    assert a == b and a.startswith("Persentase")
    assert panggilan["n"] == 1   # panggilan kedua dari cache


# ---------- T3.2: circuit breaker ----------
async def test_circuit_breaker(monkeypatch):
    async def gagal(prompt, settings, system=None):
        return None  # simulasikan kegagalan

    monkeypatch.setattr(llm, "_via_anthropic", gagal)
    s = _settings_anthropic()

    # 3 gagal beruntun (uraian beda agar tak kena cache) → sirkuit terbuka.
    for i in range(llm._CB_AMBANG):
        assert await llm.rumuskan_outcome(f"Jumlah objek {i}", tipologi="output", settings=s) is None
    assert llm._circuit["buka_sampai"] > 0  # sirkuit terbuka

    # Saat terbuka, panggilan dilewati tanpa memanggil provider.
    dipanggil = {"n": 0}

    async def hitung(prompt, settings, system=None):
        dipanggil["n"] += 1
        return "x"

    monkeypatch.setattr(llm, "_via_anthropic", hitung)
    assert await llm.rumuskan_outcome("Jumlah lain", tipologi="output", settings=s) is None
    assert dipanggil["n"] == 0


# ---------- T3.3: prompt diperkaya (few-shot + sasaran + satuan) ----------
def test_prompt_diperkaya():
    p = llm._prompt("Jumlah sekolah", satuan="unit", tipologi="output",
                    sasaran="Meningkatnya mutu pendidikan")
    assert "Contoh:" in p                              # few-shot
    assert "Meningkatnya mutu pendidikan" in p         # konteks sasaran
    assert "unit" in p                                 # satuan


# ---------- T3.4: deteksi mislabel via LLM ----------
async def test_deteksi_mislabel_llm(monkeypatch):
    async def jawab_tidak(prompt, settings, system=None):
        return "TIDAK"

    monkeypatch.setattr(llm, "_via_anthropic", jawab_tidak)
    s = _settings_anthropic()
    assert await llm.deteksi_mislabel_llm("Jumlah sekolah", "outcome", settings=s) is True

    async def jawab_sesuai(prompt, settings, system=None):
        return "SESUAI"

    monkeypatch.setattr(llm, "_via_anthropic", jawab_sesuai)
    assert await llm.deteksi_mislabel_llm("Indeks kepuasan masyarakat", "outcome", settings=s) is False


async def test_deteksi_mislabel_tanpa_penyedia(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    s = Settings(bot_token="x", webhook_secret="x" * 16, public_base_url="https://x", _env_file=None)
    assert await llm.deteksi_mislabel_llm("Jumlah sekolah", "outcome", settings=s) is None


# ---------- T3.5: saran lanjutan (advisory) ----------
def test_saran_lanjutan():
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
    from agent.improver import saran_lanjutan

    dosir = DosirKinerja(
        meta=Meta(instansi="Uji", opd_id=1, tahun=2026, dibuat_pada=datetime.now(UTC)),
        perencanaan=Perencanaan(sasaran_strategis=[SasaranStrategis(kode="1", uraian="S", indikator=[
            Indikator(indikator_id="A", uraian="Jumlah x", tipologi="output"),
        ])]),
        pengukuran=Pengukuran(capaian=[Capaian(indikator_id="A", target=100, realisasi=50,
                                               persen_capaian=50.0)]),
    )
    saran = saran_lanjutan(evaluasi_lke(dosir))
    # Ada gap Pelaporan & Evaluasi Internal (semua flag False) + Capaian rendah → saran muncul.
    assert any("Pelaporan Kinerja" in x for x in saran)
    assert any("Evaluasi Akuntabilitas Kinerja Internal" in x for x in saran)
