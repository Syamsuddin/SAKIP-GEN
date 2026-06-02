"""Kelola webhook Telegram di produksi: set | info | delete.

  python -m deploy.manage_webhook set
  python -m deploy.manage_webhook info
  python -m deploy.manage_webhook delete

Membaca BOT_TOKEN, PUBLIC_BASE_URL, WEBHOOK_SECRET dari .env.
"""
from __future__ import annotations

import asyncio
import sys

from aiogram import Bot

from config import get_settings


async def main(cmd: str) -> int:
    s = get_settings()
    bot = Bot(token=s.bot_token)
    try:
        if cmd == "set":
            ok = await bot.set_webhook(
                url=s.webhook_url, secret_token=s.webhook_secret, drop_pending_updates=True
            )
            print("set_webhook:", ok, "->", s.webhook_url)
        elif cmd == "info":
            info = await bot.get_webhook_info()
            print("url                :", info.url)
            print("pending_update_count:", info.pending_update_count)
            print("last_error_message :", info.last_error_message)
        elif cmd == "delete":
            ok = await bot.delete_webhook(drop_pending_updates=False)
            print("delete_webhook:", ok)
        else:
            print("Perintah tak dikenal. Gunakan: set | info | delete")
            return 2
    finally:
        await bot.session.close()
    return 0


if __name__ == "__main__":
    perintah = sys.argv[1] if len(sys.argv) > 1 else "info"
    raise SystemExit(asyncio.run(main(perintah)))
