"""Uji Fase 4 — robustness & observability: penjaga-drift skema agen (T4.1),
invarian status (T4.2), dan endpoint /metrics (T4.4)."""
from __future__ import annotations

import os

import httpx
import pytest_asyncio
from sqlalchemy import text as sqltext
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool

import metrics
from db.schema import buat_skema_agen


def _sqlite():
    return create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )


async def _kolom(engine, tabel: str) -> set[str]:
    async with engine.connect() as c:
        rows = (await c.execute(sqltext(f"PRAGMA table_info('{tabel}')"))).all()
    return {r[1] for r in rows}


# ---------- T4.1: penjaga drift — Core MetaData vs *_SCHEMA_SQLITE ----------
async def test_drift_skema_agen():
    from bot.auth_sql import AUTH_SCHEMA_SQLITE
    from db.events import EVENT_SCHEMA_SQLITE
    from db.promote import AUDIT_SCHEMA_SQLITE
    from db.staging import STAGING_SCHEMA_SQLITE

    core = _sqlite()
    await buat_skema_agen(core)  # semua tabel dari definisi kanonik

    legacy = _sqlite()
    async with legacy.begin() as conn:
        for skema in (STAGING_SCHEMA_SQLITE, AUDIT_SCHEMA_SQLITE, EVENT_SCHEMA_SQLITE,
                      AUTH_SCHEMA_SQLITE):
            for stmt in filter(str.strip, skema.split(";")):
                await conn.execute(sqltext(stmt))

    for tabel in ("ai_usulan", "ai_audit", "ai_event", "bot_users", "registration_codes"):
        assert await _kolom(core, tabel) == await _kolom(legacy, tabel), f"drift kolom: {tabel}"

    await core.dispose()
    await legacy.dispose()


# ---------- T4.2: status otoritatif dari kolom, bukan payload ----------
async def test_status_invarian_kolom_otoritatif():
    from agent.usulan import PerubahanField, UsulanPerbaikan
    from db.engines import set_staging_engine
    from db.staging import ambil_usulan, simpan_draft

    eng = _sqlite()
    await buat_skema_agen(eng)
    set_staging_engine(eng)

    u = UsulanPerbaikan(
        instansi="X", opd_id=1, tahun=2026, indikator_id="IKU-1.1",
        perubahan=[PerubahanField(field="tipologi", lama="output", usulan="outcome")],
        hash_data_lama="a" * 64,
    )
    uid = await simpan_draft(u)

    # Ubah HANYA kolom status; payload tetap memuat status 'draft'.
    async with eng.begin() as conn:
        await conn.execute(
            sqltext("UPDATE ai_usulan SET status='disetujui' WHERE id=:i"), {"i": uid}
        )
    got = await ambil_usulan(uid)
    assert got is not None and got.status == "disetujui"  # kolom otoritatif

    await eng.dispose()


# ---------- T4.4: endpoint /metrics ----------
@pytest_asyncio.fixture
async def _app_client():
    os.environ.update({
        "BOT_TOKEN": "12345:TEST", "WEBHOOK_SECRET": "whsec-panjang-sekali",
        "PUBLIC_BASE_URL": "https://example.test",
        "SET_WEBHOOK_ON_STARTUP": "false", "ENABLE_SCHEDULER": "false",
    })
    import config
    config.get_settings.cache_clear()
    import app as appmod
    transport = httpx.ASGITransport(app=appmod.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    config.get_settings.cache_clear()


async def test_metrics_endpoint(_app_client):
    metrics.reset()
    metrics.inc("sakipgen_evaluasi_total")
    metrics.inc("sakipgen_penerapan_total", hasil="ok")

    r = await _app_client.get("/metrics")
    assert r.status_code == 200
    assert "text/plain" in r.headers["content-type"]
    body = r.text
    assert "# TYPE sakipgen_evaluasi_total counter" in body
    assert "sakipgen_evaluasi_total 1.0" in body
    assert 'sakipgen_penerapan_total{hasil="ok"} 1.0' in body


def test_metrics_render_format():
    metrics.reset()
    metrics.inc("sakipgen_llm_total", hasil="ok")
    metrics.inc("sakipgen_llm_total", hasil="ok")
    out = metrics.render()
    assert 'sakipgen_llm_total{hasil="ok"} 2.0' in out
    assert out.count("# HELP sakipgen_llm_total") == 1  # HELP sekali per metrik
