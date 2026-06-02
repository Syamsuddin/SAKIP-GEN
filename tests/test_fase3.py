"""Uji Fase 3: improver, token, validasi initData, staging, dan route simpan."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import urllib.parse

import httpx
import pytest_asyncio
from sqlalchemy import text as sqltext
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool

from db.engines import set_ro_engine, set_staging_engine
from db.staging import STAGING_SCHEMA_SQLITE
from demo_evaluasi import build_demo_engine


# ---------- Fixtures ----------
@pytest_asyncio.fixture
async def demo_ro():
    eng = await build_demo_engine()
    set_ro_engine(eng)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def staging_db():
    eng = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with eng.begin() as conn:
        for stmt in filter(str.strip, STAGING_SCHEMA_SQLITE.split(";")):
            await conn.execute(sqltext(stmt))
    set_staging_engine(eng)
    yield eng
    await eng.dispose()


def _build_init_data(bot_token: str, user: dict) -> str:
    params = {
        "auth_date": str(int(time.time())),
        "query_id": "AAHdF6IQAAAAAN0XohDhrOrc",
        "user": json.dumps(user, separators=(",", ":")),
    }
    dcs = "\n".join(f"{k}={params[k]}" for k in sorted(params))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    params["hash"] = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
    return urllib.parse.urlencode(params)


# ---------- Improver ----------
async def test_improver(demo_ro):
    from agent.improver import usulkan_dari_gap, usulkan_perbaikan_indikator
    from agent.service import evaluasi_opd

    dosir, hasil = await evaluasi_opd(1, 2026)
    kand = usulkan_dari_gap(dosir, hasil, maksimal=5)
    assert len(kand) == 2  # IKU-1.1 & IKU-2.2 (output)
    u = kand[0]
    assert any(p.field == "tipologi" and p.usulan == "outcome" for p in u.perubahan)
    assert len(u.hash_data_lama) == 64
    from agent.evaluator import get_bobot
    assert u.estimasi_poin == round(get_bobot()["Perencanaan Kinerja"] / 100 * 60 / 4, 2)
    assert usulkan_perbaikan_indikator(dosir, hasil, "IKU-1.2") is None  # sudah outcome


# ---------- Token ----------
def test_token_roundtrip():
    from web.security import baca_token, buat_token

    t = buat_token(7, 4242, secret="rahasia")
    assert baca_token(t, secret="rahasia") == {"u": 7, "t": 4242}
    assert baca_token(t + "abc", secret="rahasia") is None
    assert baca_token(t, secret="lain") is None


# ---------- Validasi initData ----------
def test_validasi_init_data():
    from web.security import validasi_init_data

    token = "12345:TEST-BOT-TOKEN"
    init = _build_init_data(token, {"id": 4242, "first_name": "Uji"})
    assert validasi_init_data(init, bot_token=token) == 4242
    assert validasi_init_data(init + "tamper", bot_token=token) is None
    assert validasi_init_data(init, bot_token="99:WRONG") is None


# ---------- Staging roundtrip ----------
async def test_staging_roundtrip(staging_db):
    from agent.usulan import PerubahanField, UsulanPerbaikan
    from db.staging import ambil_usulan, putuskan_usulan, simpan_draft

    u = UsulanPerbaikan(
        instansi="Dinas X", opd_id=1, tahun=2026, indikator_id="IKU-1.1",
        perubahan=[PerubahanField(field="tipologi", lama="output", usulan="outcome")],
        alasan="rumus ulang", gap_lke="Perencanaan Kinerja",
        estimasi_poin=4.5, hash_data_lama="a" * 64,
    )
    uid = await simpan_draft(u)
    assert isinstance(uid, int) and uid >= 1

    got = await ambil_usulan(uid)
    assert got is not None and got.id == uid and got.status == "draft"
    assert got.indikator_id == "IKU-1.1"

    ok = await putuskan_usulan(
        uid, ditinjau_oleh="Andi", status="disetujui",
        perubahan=[
            {"field": "tipologi", "lama": "output", "usulan": "outcome"},
            {"field": "uraian", "lama": "Jumlah X", "usulan": "Persentase X"},
        ],
        alasan="oke",
    )
    assert ok
    got2 = await ambil_usulan(uid)
    assert got2.status == "disetujui" and got2.ditinjau_oleh == "Andi"
    assert len(got2.perubahan) == 2 and got2.alasan == "oke"


# ---------- Route simpan (end-to-end via ASGI) ----------
async def test_route_simpan(monkeypatch):
    os.environ.update({
        "BOT_TOKEN": "12345:TEST", "WEBHOOK_SECRET": "whsec",
        "PUBLIC_BASE_URL": "https://example.test", "TOKEN_SECRET": "tok-secret",
        "SET_WEBHOOK_ON_STARTUP": "false", "ENABLE_SCHEDULER": "false",
    })
    import config
    config.get_settings.cache_clear()

    # Engine RO (demo) + staging (SQLite)
    ro = await build_demo_engine()
    set_ro_engine(ro)
    st = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with st.begin() as conn:
        for stmt in filter(str.strip, STAGING_SCHEMA_SQLITE.split(";")):
            await conn.execute(sqltext(stmt))
    set_staging_engine(st)

    # Pengguna terdaftar (akses OPD 1)
    from bot.auth import InMemoryAuthRepository, User, set_repo
    repo = InMemoryAuthRepository()
    repo.tambah(User(telegram_id=4242, nama="Andi", peran="operator", opd_ids=[1]))
    set_repo(repo)

    # Draft dari improver
    from agent.improver import usulkan_dari_gap
    from agent.service import evaluasi_opd
    from db.staging import simpan_draft
    from web.security import buat_token

    dosir, hasil = await evaluasi_opd(1, 2026)
    u = usulkan_dari_gap(dosir, hasil, maksimal=1)[0]
    uid = await simpan_draft(u)
    token = buat_token(uid, 4242)

    import app as appmod
    monkeypatch.setattr("web.routes.validasi_init_data", lambda init, bot_token=None: 4242)

    transport = httpx.ASGITransport(app=appmod.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        rg = await client.get(f"/usulan?t={token}")
        assert rg.status_code == 200
        assert u.indikator_id in rg.text and "Simpan ke usulan" in rg.text

        ok = await client.post("/api/usulan/simpan", json={
            "initData": "x", "token": token,
            "data": {
                "perubahan": [{"field": "tipologi", "lama": "output", "usulan": "outcome"}],
                "alasan": "setuju", "hash_data_lama": u.hash_data_lama,
            },
        })
        assert ok.status_code == 200, ok.text
        assert ok.json()["status"] == "disetujui"

        konflik = await client.post("/api/usulan/simpan", json={
            "initData": "x", "token": token,
            "data": {"perubahan": [], "alasan": "x", "hash_data_lama": "salah"},
        })
        assert konflik.status_code == 409

        token_buruk = await client.post("/api/usulan/simpan", json={
            "initData": "x", "token": "garbage",
            "data": {"perubahan": [], "alasan": "x", "hash_data_lama": u.hash_data_lama},
        })
        assert token_buruk.status_code == 403

    await ro.dispose()
    await st.dispose()
