"""Middleware audit (Fase 5): catat tiap perintah/callback ke event log."""
from __future__ import annotations

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from bot.auth import resolve_user
from db.events import catat


class AuditMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if isinstance(event, Message):
            aksi, ringkas = "pesan", (event.text or "")[:160]
        elif isinstance(event, CallbackQuery):
            aksi, ringkas = "callback", (event.data or "")[:160]
        else:
            return await handler(event, data)

        uid = getattr(getattr(event, "from_user", None), "id", None)
        nama = peran = None
        if uid is not None:
            try:
                u = await resolve_user(uid)
            except Exception:  # noqa: BLE001
                u = None
            if u is not None:
                nama, peran = u.nama, u.peran
        await catat("perintah", aksi, telegram_id=uid, nama=nama, peran=peran, ringkas=ringkas)
        return await handler(event, data)
