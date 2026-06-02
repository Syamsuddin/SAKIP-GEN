"""Menu perintah Telegram per peran (setMyCommands per scope).

Telegram tak mengenal "peran" aplikasi, jadi menu per-peran dipasang per-CHAT
(scope chat = telegram_id pengguna di chat privat). Menu UMUM dipasang sebagai
default global. Dipanggil saat startup (default + tiap admin) dan setelah /daftar
berhasil (menu sesuai peran pengguna). Hanya memuat perintah yang BENAR-BENAR ada.
"""
from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

logger = logging.getLogger("sakip-gen.menu")


def _cmd(perintah: str, deskripsi: str) -> BotCommand:
    return BotCommand(command=perintah, description=deskripsi)


# Menu UMUM (default global) — perintah yang relevan untuk semua pengguna.
MENU_UMUM: list[BotCommand] = [
    _cmd("nilai", "Skor & predikat AKIP suatu OPD"),
    _cmd("capaian", "Target vs realisasi indikator"),
    _cmd("opd", "Daftar/cari OPD"),
    _cmd("status", "Akun, peran, & hak akses Anda"),
    _cmd("help", "Bantuan & daftar perintah"),
]

# Menu per peran (operator≈Kasubbag Perencanaan, kepala_dinas≈Kadis, admin≈Evaluator/Admin).
MENU_PERAN: dict[str, list[BotCommand]] = {
    "operator": [
        _cmd("rencana", "Perencanaan: sasaran, IKU, keselarasan"),
        _cmd("capaian", "Target vs realisasi (per periode)"),
        _cmd("nilai", "Skor & predikat AKIP"),
        _cmd("gap", "Kelemahan prioritas (estimasi)"),
        _cmd("usul", "Usulan perbaikan indikator"),
        _cmd("laporan", "Draft bahan LKjIP"),
        _cmd("temuan", "Temuan & tindak lanjut"),
        _cmd("dokumen", "Telusur dokumen SAKIP"),
    ],
    "kepala_dinas": [
        _cmd("nilai", "Skor & predikat AKIP"),
        _cmd("capaian", "Target vs realisasi"),
        _cmd("gap", "Kelemahan prioritas"),
        _cmd("tren", "Tren antar-tahun"),
        _cmd("benchmark", "Peringkat antar-OPD"),
        _cmd("laporan", "Draft bahan LKjIP"),
        _cmd("usulan", "Daftar usulan perbaikan"),
        _cmd("terapkan", "Terapkan usulan ke data sumber"),
    ],
    "admin": [
        _cmd("nilai", "Skor & predikat AKIP"),
        _cmd("benchmark", "Peringkat antar-OPD"),
        _cmd("temuan", "Temuan & tindak lanjut"),
        _cmd("rencana", "Perencanaan & keselarasan"),
        _cmd("capaian", "Target vs realisasi"),
        _cmd("dokumen", "Telusur dokumen SAKIP"),
        _cmd("usulan", "Daftar usulan perbaikan"),
        _cmd("terapkan", "Terapkan usulan ke data sumber"),
    ],
}


async def pasang_menu_untuk(bot: Bot, chat_id: int, peran: str) -> None:
    """Pasang menu sesuai peran pada chat privat pengguna. Best-effort (tak menggagalkan alur)."""
    perintah = MENU_PERAN.get(peran, MENU_PERAN["operator"])
    try:
        await bot.set_my_commands(perintah, scope=BotCommandScopeChat(chat_id=chat_id))
    except Exception as exc:  # noqa: BLE001 — menu kosmetik; jangan ganggu /daftar
        logger.warning("Gagal memasang menu peran '%s' untuk chat %s: %s", peran, chat_id, exc)


async def pasang_menu_startup(bot: Bot, admin_ids: set[int] | None = None) -> None:
    """Set menu default global + menu admin untuk tiap admin allowlist (saat startup)."""
    try:
        await bot.set_my_commands(MENU_UMUM, scope=BotCommandScopeDefault())
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gagal memasang menu default: %s", exc)
        return
    for aid in admin_ids or set():
        await pasang_menu_untuk(bot, aid, "admin")
    logger.info("Menu perintah Telegram terpasang (default + %d admin).", len(admin_ids or set()))
