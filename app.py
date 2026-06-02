# SPDX-License-Identifier: MIT
# SAKIP-Gen — Evaluator + Drafter untuk SAKIP PermenPAN-RB 88/2021
# Lihat LICENSE untuk detail MIT License.

"""Entrypoint SAKIP-Gen: FastAPI (healthcheck, webhook Telegram, Mini App usulan)
plus penjadwal push. Fase 5 menambah security headers, access-log + request-id,
rate limit API, perbandingan secret konstan-waktu, dan audit konfigurasi saat startup.

Produksi : gunicorn app:app -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000
Lokal    : uvicorn app:app --reload  (set SET_WEBHOOK_ON_STARTUP=false bila tanpa HTTPS)
"""
import hmac
import logging
from contextlib import asynccontextmanager

from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse

import metrics
from bot.instance import bot, dp
from bot.menu import pasang_menu_startup
from bot.scheduler import start_scheduler, stop_scheduler
from config import audit_keamanan, get_settings
from db.engines import get_promote_engine, get_ro_engine, get_staging_engine
from web.health import readiness
from web.middleware import RequestContextMiddleware, SecurityHeadersMiddleware
from web.routes import router as web_router

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger("sakip-gen")


@asynccontextmanager
async def lifespan(_: FastAPI):
    for w in audit_keamanan(settings):
        logger.warning("KEAMANAN: %s", w)
    if settings.set_webhook_on_startup:
        await bot.set_webhook(
            url=settings.webhook_url,
            secret_token=settings.webhook_secret,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True,
        )
        logger.info("Webhook diset ke %s", settings.webhook_url)
    else:
        logger.info("SET_WEBHOOK_ON_STARTUP=false — webhook tidak diset saat startup.")
    await pasang_menu_startup(bot, settings.admin_id_set)
    if settings.enable_scheduler:
        start_scheduler(bot)
        logger.info("Penjadwal ringkasan triwulanan aktif.")
    try:
        yield
    finally:
        if settings.enable_scheduler:
            stop_scheduler()
        if settings.set_webhook_on_startup:
            await bot.delete_webhook()
        await bot.session.close()
        logger.info("Sesi bot ditutup.")


app = FastAPI(title="SAKIP-Gen", version="1.0.0", lifespan=lifespan)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestContextMiddleware, max_body_bytes=settings.max_body_bytes)
app.include_router(web_router)


@app.exception_handler(Exception)
async def _tangani_galat(request: Request, exc: Exception) -> JSONResponse:
    rid = getattr(request.state, "request_id", "-")
    metrics.inc("sakipgen_error_total")
    logger.exception("Kesalahan tak tertangani (rid=%s)", rid)
    return JSONResponse(
        {"detail": "Terjadi kesalahan internal.", "request_id": rid}, status_code=500
    )


@app.get("/metrics")
async def metrics_endpoint() -> PlainTextResponse:
    return PlainTextResponse(metrics.render(), media_type="text/plain; version=0.0.4")


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "service": "sakip-gen", "version": app.version}


@app.get("/readyz")
async def readyz() -> JSONResponse:
    ok, checks = await readiness([
        ("ro", get_ro_engine),
        ("staging", get_staging_engine),
        ("promote", get_promote_engine),
    ])
    return JSONResponse({"ready": ok, "checks": checks}, status_code=200 if ok else 503)


@app.post(settings.webhook_path)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> JSONResponse:
    token = x_telegram_bot_api_secret_token or ""
    if not hmac.compare_digest(token, settings.webhook_secret):
        logger.warning("Webhook ditolak: secret tidak cocok.")
        raise HTTPException(status_code=403, detail="forbidden")
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return JSONResponse({"ok": True})
