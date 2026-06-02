"""Handler dasar: perkenalan, bantuan, ping, dan fallback.

Router ini didaftarkan TERAKHIR agar perintah spesifik (bot/kinerja.py)
dicocokkan lebih dulu dan fallback menjadi handler paling akhir.
"""
from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

router = Router(name="base")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Halo! Saya <b>SAKIP-Gen</b> — asisten evaluasi dan perbaikan SAKIP.\n\n"
        "Jika belum terdaftar, kirim <code>/daftar &lt;kode&gt;</code> dengan kode dari admin.\n"
        "Ketik /help untuk melihat perintah."
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "<b>Perintah</b>\n"
        "/daftar &lt;kode&gt; — mendaftar memakai kode\n"
        "/evaluasi &lt;opd_id&gt; [tahun] — evaluasi LKE satu OPD\n"
        "/gap &lt;opd_id&gt; [tahun] — daftar gap prioritas\n"
        "/status — status akun & akses Anda\n"
        "/ping — cek kesehatan bot"
    )


@router.message(Command("ping"))
async def cmd_ping(message: Message) -> None:
    await message.answer("pong — SAKIP-Gen aktif.")


@router.message()
async def fallback(message: Message) -> None:
    await message.answer("Perintah tidak dikenali. Ketik /help untuk daftar perintah.")
