"""Autentikasi & otorisasi SAKIP-Gen: allowlist pengguna + RBAC sederhana.

Pengguna mendaftar dengan kode sekali-pakai (di produksi diterbitkan eSAKIP),
yang mengikat telegram_id ke identitas + peran + daftar OPD yang boleh diakses.
Repo default in-memory; untuk produksi, ganti dengan repo berbasis tabel
(mis. sakip_ai.bot_users) lewat set_repo().
"""
from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from config import get_settings

logger = logging.getLogger("sakip-gen.auth")


@dataclass
class User:
    telegram_id: int
    nama: str
    peran: str = "operator"          # operator | kepala_dinas | admin
    opd_ids: list[int] = field(default_factory=list)

    @property
    def is_admin(self) -> bool:
        return self.peran == "admin"

    def boleh_opd(self, opd_id: int) -> bool:
        return self.is_admin or opd_id in self.opd_ids

    def boleh_promosi(self) -> bool:
        """Hak menerapkan usulan ke tabel sumber (Fase 4)."""
        return self.peran in {"kepala_dinas", "admin"}


class AuthRepository(Protocol):
    async def get_user(self, telegram_id: int) -> User | None: ...
    async def register(self, telegram_id: int, kode: str) -> User | None: ...
    async def all_users(self) -> list[User]: ...


class InMemoryAuthRepository:
    """Repo in-memory. Kode pendaftaran: {kode: {nama, peran, opd_ids}}."""

    def __init__(self, kode_pendaftaran: dict[str, dict] | None = None) -> None:
        self._users: dict[int, User] = {}
        self._kode: dict[str, dict] = dict(kode_pendaftaran or {})

    async def get_user(self, telegram_id: int) -> User | None:
        return self._users.get(telegram_id)

    async def register(self, telegram_id: int, kode: str) -> User | None:
        info = self._kode.pop(kode, None)   # sekali-pakai
        if info is None:
            return None
        user = User(
            telegram_id=telegram_id, nama=info.get("nama", f"User {telegram_id}"),
            peran=info.get("peran", "operator"), opd_ids=list(info.get("opd_ids", [])),
        )
        self._users[telegram_id] = user
        return user

    async def all_users(self) -> list[User]:
        return list(self._users.values())

    def tambah(self, user: User) -> None:
        """Sisipkan pengguna langsung (untuk seeding/pengujian)."""
        self._users[user.telegram_id] = user


_repo: AuthRepository | None = None


def _kode_dari_config() -> dict:
    raw = get_settings().registration_codes
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("REGISTRATION_CODES bukan JSON valid; diabaikan.")
        return {}


def get_repo() -> AuthRepository:
    global _repo
    if _repo is None:
        if get_settings().use_sql_auth:
            from bot.auth_sql import SqlAuthRepository
            _repo = SqlAuthRepository()
        else:
            _repo = InMemoryAuthRepository(_kode_dari_config())
    return _repo


def set_repo(repo: AuthRepository) -> None:
    global _repo
    _repo = repo


async def resolve_user(telegram_id: int | None) -> User | None:
    """User efektif: gabungkan repo pendaftaran + allowlist admin (ADMIN_TELEGRAM_IDS).

    telegram_id pada allowlist selalu berperan admin (akses bot tanpa /daftar). Bila
    sudah terdaftar namun bukan admin, perannya dinaikkan ke admin (nama dipertahankan).
    """
    if telegram_id is None:
        return None
    user = await get_repo().get_user(telegram_id)
    if telegram_id in get_settings().admin_id_set:
        if user is None:
            return User(telegram_id=telegram_id, nama=f"Admin {telegram_id}", peran="admin")
        if user.peran != "admin":
            return User(telegram_id=user.telegram_id, nama=user.nama,
                        peran="admin", opd_ids=user.opd_ids)
    return user


class AuthMiddleware(BaseMiddleware):
    """Menyuntikkan `user` ke handler dan memblokir pengguna tak terdaftar.

    Perintah publik (/start, /help, /daftar) tetap diizinkan tanpa pendaftaran.
    """

    PUBLIC_PREFIXES = ("/start", "/help", "/daftar")

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tid = getattr(getattr(event, "from_user", None), "id", None)
        user = await resolve_user(tid)
        data["user"] = user

        text = getattr(event, "text", None) or ""
        is_public = text.startswith(self.PUBLIC_PREFIXES)
        if user is None and not is_public:
            answer = getattr(event, "answer", None)
            if answer is not None:
                await answer(
                    "Anda belum terdaftar untuk memakai SAKIP-Gen.\n"
                    "Kirim <code>/daftar &lt;kode&gt;</code> dengan kode dari admin."
                )
            return None
        return await handler(event, data)
