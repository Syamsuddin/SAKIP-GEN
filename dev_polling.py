"""Mode long-polling untuk pengembangan lokal (tanpa HTTPS/webhook)."""
import asyncio
import logging

from bot.instance import bot, dp
from bot.menu import pasang_menu_startup
from bot.scheduler import start_scheduler, stop_scheduler
from config import get_settings


async def main() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    logging.getLogger("sakip-gen").info("Memulai long-polling (mode pengembangan).")
    if settings.enable_scheduler:
        start_scheduler(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await pasang_menu_startup(bot, settings.admin_id_set)
    try:
        await dp.start_polling(bot)
    finally:
        stop_scheduler()


if __name__ == "__main__":
    asyncio.run(main())
