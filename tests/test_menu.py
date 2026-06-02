"""Uji menu perintah per peran: hanya memuat perintah yang benar-benar terdaftar,
dan pemasangan per-scope dipanggil dengan benar (best-effort, tak menggagalkan alur)."""
from __future__ import annotations

from bot.menu import MENU_PERAN, MENU_UMUM, pasang_menu_startup, pasang_menu_untuk

# Perintah yang BENAR-BENAR didaftarkan di bot/kinerja.py + bot/handlers.py.
PERINTAH_NYATA = {
    "daftar", "evaluasi", "nilai", "gap", "tren", "benchmark", "usul", "usulan",
    "terapkan", "status", "opd", "rencana", "capaian", "laporan", "temuan", "dokumen",
    "start", "help", "ping",
}


def test_menu_hanya_perintah_nyata():
    semua = list(MENU_UMUM) + [c for cmds in MENU_PERAN.values() for c in cmds]
    for c in semua:
        assert c.command in PERINTAH_NYATA, f"perintah menu tak terdaftar: /{c.command}"
        assert c.description, "deskripsi menu wajib diisi"


def test_menu_peran_lengkap():
    assert set(MENU_PERAN) >= {"operator", "kepala_dinas", "admin"}
    # terapkan hanya untuk peran berwenang promosi.
    assert any(c.command == "terapkan" for c in MENU_PERAN["kepala_dinas"])
    assert not any(c.command == "terapkan" for c in MENU_PERAN["operator"])


class _BotPalsu:
    def __init__(self):
        self.calls: list[tuple] = []

    async def set_my_commands(self, commands, scope=None):
        self.calls.append((tuple(c.command for c in commands), type(scope).__name__))


async def test_pasang_menu_untuk_fallback_operator():
    bot = _BotPalsu()
    await pasang_menu_untuk(bot, 123, "peran_tak_dikenal")
    assert bot.calls and bot.calls[0][1] == "BotCommandScopeChat"
    # Peran tak dikenal → fallback ke menu operator.
    assert bot.calls[0][0] == tuple(c.command for c in MENU_PERAN["operator"])


async def test_pasang_menu_startup_default_plus_admin():
    bot = _BotPalsu()
    await pasang_menu_startup(bot, {111, 222})
    scopes = [c[1] for c in bot.calls]
    assert scopes[0] == "BotCommandScopeDefault"          # default global lebih dulu
    assert scopes.count("BotCommandScopeChat") == 2       # satu per admin
