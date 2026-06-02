"""Uji Fase 5: throttle bot, rate limiter API, event log, audit keamanan, header HTTP."""
from __future__ import annotations

import httpx
import pytest_asyncio  # noqa: F401  (mengaktifkan mode asyncio)
from sqlalchemy import text as sqltext
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool

from db.engines import set_staging_engine
from db.events import EVENT_SCHEMA_SQLITE, ambil_peristiwa, catat


# ---------- Throttle (aiogram middleware) ----------
async def test_throttle_gating():
    from bot.throttle import ThrottleMiddleware

    mw = ThrottleMiddleware(limit=3, window=100.0)
    calls = {"n": 0}

    async def handler(event, data):
        calls["n"] += 1
        return "ok"

    class E:  # bukan Message/CallbackQuery: jalur blokir tak menjawab, gating tetap jalan
        from_user = type("U", (), {"id": 7})()

    hasil = [await mw(handler, E(), {}) for _ in range(5)]
    assert calls["n"] == 3
    assert hasil[3] is None and hasil[4] is None


def test_throttle_window():
    from bot.throttle import ThrottleMiddleware

    mw = ThrottleMiddleware(limit=2, window=10.0)
    assert mw._diizinkan(1, now=0.0) is True
    assert mw._diizinkan(1, now=1.0) is True
    assert mw._diizinkan(1, now=2.0) is False
    assert mw._diizinkan(2, now=2.0) is True       # pengguna lain bebas
    assert mw._diizinkan(1, now=11.0) is True       # window sudah lewat


# ---------- Rate limiter (API) ----------
def test_limiter():
    from web.ratelimit import SlidingWindowLimiter

    lim = SlidingWindowLimiter(limit=2, window=10.0)
    assert lim.cek("a", now=0.0)[0] is True
    assert lim.cek("a", now=1.0)[0] is True
    ok, retry = lim.cek("a", now=2.0)
    assert ok is False and retry > 0
    assert lim.cek("b", now=2.0)[0] is True          # kunci lain tak terpengaruh
    assert lim.cek("a", now=11.0)[0] is True          # window lewat


# ---------- Event log (dwi-sink, DB) ----------
async def test_event_log():
    eng = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with eng.begin() as conn:
        for stmt in filter(str.strip, EVENT_SCHEMA_SQLITE.split(";")):
            await conn.execute(sqltext(stmt))
    set_staging_engine(eng)

    await catat("perintah", "pesan", telegram_id=7, nama="Andi", peran="operator",
                ringkas="/usul 1", detail={"opd": 1})
    await catat("penerapan", "terapkan", telegram_id=9, status="ok")

    rows = await ambil_peristiwa()
    assert len(rows) == 2
    assert rows[0]["kategori"] == "penerapan" and rows[0]["aksi"] == "terapkan"
    assert any(r["telegram_id"] == 7 and r["aksi"] == "pesan" for r in rows)
    await eng.dispose()


# ---------- Audit keamanan (config) ----------
def test_audit_keamanan():
    from config import Settings, audit_keamanan

    # _env_file=None: hermetik dari .env repo agar uji deterministik.
    lemah = Settings(bot_token="x", webhook_secret="pendek",
                     public_base_url="http://contoh", env="production", _env_file=None)
    w = audit_keamanan(lemah)
    assert any("WEBHOOK_SECRET" in x for x in w)
    assert any("HTTPS" in x for x in w)
    assert any("TOKEN_SECRET" in x for x in w)
    assert any("USE_SQL_AUTH" in x for x in w)          # T1.2: peringatan auth in-memory
    assert any("jalur akses bot" in x for x in w)       # tak ada kode & tak ada admin

    kuat = Settings(bot_token="x", webhook_secret="x" * 20,
                    public_base_url="https://contoh", token_secret="y" * 20,
                    registration_codes="{}", use_sql_auth=True, env="production",
                    _env_file=None)
    assert audit_keamanan(kuat) == []

    # Admin allowlist saja sudah memenuhi "jalur akses bot" (tanpa registration_codes).
    via_admin = Settings(bot_token="x", webhook_secret="x" * 20,
                         public_base_url="https://contoh", token_secret="y" * 20,
                         admin_telegram_ids="207118312", use_sql_auth=True,
                         env="production", _env_file=None)
    assert not any("jalur akses bot" in x for x in audit_keamanan(via_admin))

    dev = Settings(bot_token="x", webhook_secret="p",
                   public_base_url="http://c", env="development", _env_file=None)
    assert audit_keamanan(dev) == []


# ---------- Header keamanan + batas body (middleware HTTP) ----------
async def test_http_middleware():
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route

    from web.middleware import RequestContextMiddleware, SecurityHeadersMiddleware

    async def ep(request):
        return PlainTextResponse("ok")

    app = Starlette(routes=[Route("/x", ep, methods=["GET", "POST"])])
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestContextMiddleware, max_body_bytes=10)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.get("/x")
        assert r.status_code == 200
        assert "Content-Security-Policy" in r.headers
        assert r.headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Request-ID" in r.headers
        big = await c.post("/x", content=b"x" * 50)
        assert big.status_code == 413


# ---------- Webhook: perbandingan secret konstan-waktu ----------
def test_webhook_compare():
    import hmac
    assert hmac.compare_digest("rahasia", "rahasia") is True
    assert hmac.compare_digest("rahasia", "salah") is False
