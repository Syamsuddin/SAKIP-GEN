# SPDX-License-Identifier: MIT
# SAKIP-Gen — Evaluator + Drafter untuk SAKIP PermenPAN-RB 88/2021
# Lihat LICENSE untuk detail MIT License.

"""Instance Bot & Dispatcher aiogram: middleware (throttle, audit, auth) + router."""
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.audit_mw import AuditMiddleware
from bot.auth import AuthMiddleware
from bot.handlers import router as base_router
from bot.kinerja import router as kinerja_router
from bot.throttle import ThrottleMiddleware
from config import get_settings

settings = get_settings()

bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()

# Urutan eksekusi: throttle (luar) -> audit -> auth (dalam) -> handler.
for _obs in (dp.message, dp.callback_query):
    _obs.middleware(ThrottleMiddleware(limit=settings.bot_rate_per_menit, window=60.0))
    _obs.middleware(AuditMiddleware())
    _obs.middleware(AuthMiddleware())

dp.include_router(kinerja_router)   # perintah & callback spesifik lebih dulu
dp.include_router(base_router)      # /start, /help, /ping, fallback (terakhir)
