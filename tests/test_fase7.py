"""Uji Fase 7: auth SQL, sambungan LLM (+fallback), readiness, dan daftar usulan."""
from __future__ import annotations

import pytest_asyncio  # noqa: F401
from sqlalchemy import text as sqltext
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool

from db.engines import set_staging_engine


def _sqlite():
    return create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )


async def _buat_skema(eng, schema_sql: str) -> None:
    async with eng.begin() as c:
        for stmt in filter(str.strip, schema_sql.split(";")):
            await c.execute(sqltext(stmt))


# ---------- Auth SQL ----------
async def test_sql_auth():
    from bot.auth import User
    from bot.auth_sql import AUTH_SCHEMA_SQLITE, SqlAuthRepository

    eng = _sqlite()
    await _buat_skema(eng, AUTH_SCHEMA_SQLITE)
    repo = SqlAuthRepository(eng)

    await repo.tambah_kode("K-1", nama="Andi", peran="operator", opd_ids=[1, 2])
    u = await repo.register(99, "K-1")
    assert u is not None and u.nama == "Andi" and u.opd_ids == [1, 2]
    assert await repo.register(100, "K-1") is None        # sekali-pakai

    g = await repo.get_user(99)
    assert g is not None and g.boleh_opd(2) and not g.boleh_opd(3)
    assert len(await repo.all_users()) == 1

    await repo.tambah(User(5, "Admin", "admin", []))       # seeding/upsert
    adm = await repo.get_user(5)
    assert adm.is_admin and adm.boleh_promosi()
    await eng.dispose()


# ---------- LLM ----------
async def test_llm_tanpa_penyedia(monkeypatch):
    from agent.llm import llm_tersedia, rumuskan_outcome
    from config import Settings

    # Isolasi penuh: abaikan env OS DAN berkas .env agar penyedia LLM benar-benar kosong.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    s = Settings(
        bot_token="x", webhook_secret="x" * 16, public_base_url="https://x",
        _env_file=None,
    )
    assert llm_tersedia(s) is False
    assert await rumuskan_outcome("Jumlah sekolah terakreditasi", settings=s) is None


async def test_llm_dengan_penyedia(monkeypatch):
    import agent.llm as llm
    from config import Settings

    async def fake(prompt, settings):
        return "Persentase sekolah terakreditasi minimal B"

    monkeypatch.setattr(llm, "_via_anthropic", fake)
    s = Settings(bot_token="x", webhook_secret="x" * 16,
                 public_base_url="https://x", anthropic_api_key="key")
    assert llm.llm_tersedia(s) is True
    out = await llm.rumuskan_outcome("Jumlah sekolah terakreditasi", tipologi="output", settings=s)
    assert out and out.startswith("Persentase")

    from agent.improver import sempurnakan_dengan_llm
    from agent.usulan import PerubahanField, UsulanPerbaikan

    u = UsulanPerbaikan(
        instansi="X", opd_id=1, tahun=2026, indikator_id="IKU-1.1",
        perubahan=[PerubahanField(field="uraian", lama="Jumlah sekolah terakreditasi",
                                  usulan="(heuristik)")],
        hash_data_lama="a" * 64,
    )
    u2 = await sempurnakan_dengan_llm(u, settings=s)
    assert next(p.usulan for p in u2.perubahan if p.field == "uraian").startswith("Persentase")


# ---------- Readiness ----------
async def test_readiness():
    from web.health import readiness

    eng = _sqlite()  # engine sehat

    def baik():
        return eng

    def belum():
        raise RuntimeError("DB_X belum diset")

    class _BadCM:
        async def __aenter__(self):
            raise Exception("connect gagal")

        async def __aexit__(self, *a):
            return False

    class _BadEngine:
        def connect(self):
            return _BadCM()

    def rusak():
        return _BadEngine()

    ok, checks = await readiness([("ro", baik), ("staging", belum)])
    assert ok is True and checks["ro"] == "ok" and checks["staging"] == "not-configured"

    ok2, checks2 = await readiness([("ro", baik), ("promote", rusak)])
    assert ok2 is False and checks2["promote"] == "fail"
    await eng.dispose()


# ---------- Daftar usulan ----------
async def test_daftar_usulan():
    from agent.usulan import PerubahanField, UsulanPerbaikan
    from db.staging import STAGING_SCHEMA_SQLITE, daftar_usulan, putuskan_usulan, simpan_draft

    eng = _sqlite()
    await _buat_skema(eng, STAGING_SCHEMA_SQLITE)
    set_staging_engine(eng)

    def mk(kode):
        return UsulanPerbaikan(
            instansi="X", opd_id=1, tahun=2026, indikator_id=kode,
            perubahan=[PerubahanField(field="tipologi", lama="output", usulan="outcome")],
            hash_data_lama="a" * 64, estimasi_poin=4.5,
        )

    await simpan_draft(mk("IKU-1.1"))
    id2 = await simpan_draft(mk("IKU-2.2"))
    await putuskan_usulan(id2, ditinjau_oleh="Andi", status="disetujui")

    assert len(await daftar_usulan([1])) == 2
    disetujui = await daftar_usulan([1], status="disetujui")
    assert len(disetujui) == 1 and disetujui[0].indikator_id == "IKU-2.2"
    assert await daftar_usulan([]) == []
    await eng.dispose()
