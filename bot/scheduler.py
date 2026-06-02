"""Penjadwal push ringkasan evaluasi (APScheduler)."""
from __future__ import annotations

import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from agent.analitik import indikator_berisiko, keselarasan_sasaran
from agent.service import evaluasi_opd
from bot.auth import get_repo
from bot.format import format_ringkasan

logger = logging.getLogger("sakip-gen.scheduler")
scheduler = AsyncIOScheduler()


def _bagian_dini(dosir) -> str:
    """Bagian peringatan dini (indikator berisiko + keselarasan) untuk push triwulanan."""
    baris: list[str] = []
    risiko = indikator_berisiko(dosir)
    if risiko:
        baris += ["", "⚠️ <b>Indikator berisiko</b> (capaian rendah):"]
        baris += [f"• {r}" for r in risiko[:5]]
    selaras = keselarasan_sasaran(dosir)
    if selaras:
        baris += ["", "🔗 <b>Keselarasan</b>:"]
        baris += [f"• {s}" for s in selaras[:5]]
    return "\n".join(baris)


async def kirim_ringkasan_terjadwal(bot, tahun: int | None = None) -> int:
    """Evaluasi OPD tiap pengguna terdaftar lalu kirim ringkasan. Kembalikan jumlah terkirim."""
    tahun = tahun or datetime.now().year
    terkirim = 0
    for u in await get_repo().all_users():
        for opd_id in u.opd_ids:
            try:
                dosir, hasil = await evaluasi_opd(opd_id, tahun)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Gagal evaluasi OPD %s untuk %s: %s", opd_id, u.telegram_id, exc)
                continue
            pesan = "<b>Ringkasan kinerja terjadwal</b>\n\n" + format_ringkasan(hasil)
            pesan += _bagian_dini(dosir)
            await bot.send_message(u.telegram_id, pesan)
            terkirim += 1
    return terkirim


def start_scheduler(bot) -> None:
    """Jadwalkan push tiap awal triwulan: 1 Jan/Apr/Jul/Okt pukul 07:00."""
    scheduler.add_job(
        kirim_ringkasan_terjadwal,
        CronTrigger(month="1,4,7,10", day=1, hour=7),
        args=[bot], id="ringkasan_triwulanan", replace_existing=True,
    )
    if not scheduler.running:
        scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
