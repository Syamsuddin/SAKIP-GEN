"""Uji Fase 2: autentikasi/RBAC, middleware, pemformat, dan push terjadwal."""
from __future__ import annotations

import pytest_asyncio

from bot.auth import AuthMiddleware, InMemoryAuthRepository, User, set_repo
from bot.format import format_gap, format_ringkasan
from bot.scheduler import kirim_ringkasan_terjadwal
from db.engines import set_ro_engine
from demo_evaluasi import build_demo_engine

KODE = {"K1": {"nama": "Budi", "peran": "operator", "opd_ids": [1, 2]}}


# ---- Auth & RBAC ----
async def test_register_single_use():
    repo = InMemoryAuthRepository(dict(KODE))
    u = await repo.register(100, "K1")
    assert u is not None and u.nama == "Budi"
    assert u.boleh_opd(1) and not u.boleh_opd(9)
    assert await repo.register(101, "K1") is None   # kode sekali-pakai
    assert (await repo.get_user(100)) is u


def test_rbac_admin():
    admin = User(telegram_id=1, nama="A", peran="admin")
    assert admin.boleh_opd(999)


# ---- Middleware ----
class _FU:
    def __init__(self, i): self.id = i


class _Ev:
    def __init__(self, uid, text):
        self.from_user = _FU(uid)
        self.text = text
        self.answered: list[str] = []

    async def answer(self, t, **k):
        self.answered.append(t)


async def _run_mw(repo, uid, text):
    set_repo(repo)
    flag = {"called": False, "data": None}

    async def handler(event, data):
        flag["called"] = True
        flag["data"] = data
        return "ok"

    ev = _Ev(uid, text)
    await AuthMiddleware()(handler, ev, {})
    return flag, ev


async def test_mw_blocks_unregistered():
    flag, ev = await _run_mw(InMemoryAuthRepository(), 7, "/evaluasi 1")
    assert flag["called"] is False
    assert ev.answered


async def test_mw_allows_public():
    flag, ev = await _run_mw(InMemoryAuthRepository(), 7, "/start")
    assert flag["called"] is True


async def test_mw_allows_registered():
    repo = InMemoryAuthRepository(dict(KODE))
    await repo.register(7, "K1")
    flag, ev = await _run_mw(repo, 7, "/evaluasi 1")
    assert flag["called"] is True
    assert flag["data"]["user"].nama == "Budi"


# ---- Admin allowlist (ADMIN_TELEGRAM_IDS) ----
def test_admin_id_set_parsing():
    from config import Settings

    s = Settings(bot_token="x", webhook_secret="x" * 16, public_base_url="https://x",
                 admin_telegram_ids="207118312, 123 ;456", _env_file=None)
    assert s.admin_id_set == {207118312, 123, 456}
    kosong = Settings(bot_token="x", webhook_secret="x" * 16, public_base_url="https://x",
                      _env_file=None)
    assert kosong.admin_id_set == set()


async def test_resolve_user_admin_allowlist(monkeypatch):
    import bot.auth as auth
    from config import Settings

    monkeypatch.setattr(
        auth, "get_settings",
        lambda: Settings(bot_token="x", webhook_secret="x" * 16,
                         public_base_url="https://x", admin_telegram_ids="207118312",
                         _env_file=None),
    )
    set_repo(InMemoryAuthRepository())

    # Belum terdaftar tapi di allowlist → admin tersintesis.
    admin = await auth.resolve_user(207118312)
    assert admin is not None and admin.is_admin and admin.boleh_promosi()
    assert admin.boleh_opd(999)  # admin akses semua OPD

    # Tidak di allowlist & tidak terdaftar → None.
    assert await auth.resolve_user(7) is None


async def test_mw_allows_admin_without_register(monkeypatch):
    import bot.auth as auth
    from config import Settings

    monkeypatch.setattr(
        auth, "get_settings",
        lambda: Settings(bot_token="x", webhook_secret="x" * 16,
                         public_base_url="https://x", admin_telegram_ids="207118312",
                         _env_file=None),
    )
    # Tanpa /daftar, perintah non-publik tetap diizinkan untuk admin allowlist.
    flag, ev = await _run_mw(InMemoryAuthRepository(), 207118312, "/evaluasi 1")
    assert flag["called"] is True
    assert flag["data"]["user"].is_admin


# ---- Pemformat + push terjadwal ----
@pytest_asyncio.fixture
async def demo_engine():
    eng = await build_demo_engine()
    set_ro_engine(eng)
    yield eng
    await eng.dispose()


class _FakeBot:
    def __init__(self):
        self.sent: list[tuple[int, str]] = []

    async def send_message(self, chat_id, text, **k):
        self.sent.append((chat_id, text))


async def test_push_terjadwal(demo_engine):
    repo = InMemoryAuthRepository()
    repo.tambah(User(telegram_id=555, nama="Kadis", peran="kepala_dinas", opd_ids=[1]))
    set_repo(repo)

    bot = _FakeBot()
    n = await kirim_ringkasan_terjadwal(bot, tahun=2026)
    assert n == 1
    chat_id, msg = bot.sent[0]
    assert chat_id == 555
    assert "Predikat" in msg and "Dinas Pendidikan" in msg
    # pemformat gap juga konsisten
    from agent.service import evaluasi_opd
    _, hasil = await evaluasi_opd(1, 2026)
    assert "Gap prioritas" in format_gap(hasil)
    assert "Estimasi nilai AKIP" in format_ringkasan(hasil)


# ---- Fase 0: kejujuran nilai (disclaimer + relabel) ----
async def test_format_disclaimer_dan_label(demo_engine):
    from agent.service import evaluasi_opd
    from bot.format import DISCLAIMER, LABEL_NILAI

    _, hasil = await evaluasi_opd(1, 2026)
    ringkasan = format_ringkasan(hasil)
    gap = format_gap(hasil)

    # Disclaimer wajib hadir di KEDUA keluaran pengguna.
    assert DISCLAIMER in ringkasan
    assert DISCLAIMER in gap
    assert "bukan hasil LKE" in DISCLAIMER

    # Label estimasi (indikatif) + predikat indikatif; selalu disertai disclaimer.
    assert LABEL_NILAI in ringkasan
    assert "Estimasi nilai AKIP" in ringkasan
    assert "Predikat (indikatif)" in ringkasan
    assert "(indikatif)" in LABEL_NILAI

    # Disclaimer juga muncul saat tidak ada gap.
    hasil.gap = []
    assert DISCLAIMER in format_gap(hasil)
