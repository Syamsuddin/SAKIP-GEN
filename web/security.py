"""Gerbang keamanan Mini App: token opaque (itsdangerous) + validasi initData.

- buat_token / baca_token: token bertanda tangan & berbatas waktu yang membawa
  {u: id_usulan, t: telegram_id} — dipakai di URL alih-alih ID mentah.
- validasi_init_data: verifikasi HMAC initData Telegram (lewat aiogram) lalu
  kembalikan telegram_id pengirim. Mengembalikan None bila tidak valid.
"""
from __future__ import annotations

import logging

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config import get_settings

logger = logging.getLogger("sakip-gen.security")
_SALT = "sakip-gen-usulan"


def _secret(secret: str | None) -> str:
    if secret:
        return secret
    s = get_settings()
    return s.token_secret or s.webhook_secret


def _serializer(secret: str | None = None) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(_secret(secret), salt=_SALT)


def buat_token(usulan_id: int, telegram_id: int, secret: str | None = None) -> str:
    return _serializer(secret).dumps({"u": int(usulan_id), "t": int(telegram_id)})


def baca_token(token: str, max_age: int = 3600, secret: str | None = None) -> dict | None:
    try:
        return _serializer(secret).loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None


def validasi_init_data(init_data: str, bot_token: str | None = None) -> int | None:
    from aiogram.utils.web_app import safe_parse_webapp_init_data

    token = bot_token or get_settings().bot_token
    try:
        data = safe_parse_webapp_init_data(token=token, init_data=init_data)
    except Exception:  # noqa: BLE001
        return None
    return data.user.id if data.user else None
