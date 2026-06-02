"""Throttle per-pengguna (Fase 5): batasi laju perintah untuk cegah spam & biaya."""
from __future__ import annotations

import logging
import time
from collections import defaultdict, deque

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

logger = logging.getLogger("sakip-gen.throttle")


class ThrottleMiddleware(BaseMiddleware):
    """Sliding-window per telegram_id: maksimum `limit` peristiwa per `window` detik."""

    def __init__(self, limit: int = 20, window: float = 60.0) -> None:
        self.limit = limit
        self.window = window
        self._hits: dict[int, deque[float]] = defaultdict(deque)

    def _diizinkan(self, uid: int, now: float) -> bool:
        dq = self._hits[uid]
        batas = now - self.window
        while dq and dq[0] < batas:
            dq.popleft()
        if len(dq) >= self.limit:
            return False
        dq.append(now)
        return True

    async def __call__(self, handler, event, data):
        uid = getattr(getattr(event, "from_user", None), "id", None)
        if uid is not None and not self._diizinkan(uid, time.monotonic()):
            logger.info("Throttle: pengguna %s dibatasi.", uid)
            pesan = "Terlalu banyak permintaan. Mohon tunggu sebentar lalu coba lagi."
            if isinstance(event, Message):
                await event.answer(pesan)
            elif isinstance(event, CallbackQuery):
                await event.answer(pesan, show_alert=False)
            return None  # hentikan rantai pemrosesan
        return await handler(event, data)
