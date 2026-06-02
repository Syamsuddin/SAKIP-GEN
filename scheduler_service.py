"""Service penjadwal MANDIRI (Fase 5, T5.1) — jalankan terpisah dari web saat multi-worker.

Saat web dijalankan dengan banyak worker, set `ENABLE_SCHEDULER=false` di web dan jalankan
SATU instans proses ini agar push triwulanan tidak ganda:

    ENABLE_SCHEDULER=false gunicorn app:app -c deploy/gunicorn.conf.py   # WORKERS=N
    python scheduler_service.py                                          # satu instans

Memerlukan auth SQL (USE_SQL_AUTH=true) agar daftar pengguna konsisten dengan web.
"""
from __future__ import annotations

import asyncio
import logging
import signal

from bot.instance import bot
from bot.scheduler import start_scheduler, stop_scheduler
from config import get_settings


async def main() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    log = logging.getLogger("sakip-gen.scheduler-service")
    start_scheduler(bot)
    log.info("Penjadwal mandiri aktif (push triwulanan). Ctrl+C / SIGTERM untuk berhenti.")

    berhenti = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, berhenti.set)
        except NotImplementedError:  # platform tanpa add_signal_handler
            pass
    try:
        await berhenti.wait()
    finally:
        stop_scheduler()
        await bot.session.close()
        log.info("Penjadwal mandiri berhenti.")


if __name__ == "__main__":
    asyncio.run(main())
