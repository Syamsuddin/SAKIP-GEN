"""Pembatas laju API (Fase 5).

Default in-memory (per-proses; cocok 1 worker). Untuk multi-worker (T5.1), set
`REDIS_URL` → `buat_limiter()` mengembalikan limiter berbasis Redis dengan antarmuka
`cek_async()` yang sama, sehingga laju konsisten lintas worker.
"""
from __future__ import annotations

import os
import time
from collections import defaultdict, deque

from fastapi import Request


class SlidingWindowLimiter:
    """Sliding window in-memory. `cek()` sinkron; `cek_async()` membungkusnya."""

    def __init__(self, limit: int, window: float = 60.0) -> None:
        self.limit = limit
        self.window = window
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def cek(self, kunci: str, now: float | None = None) -> tuple[bool, float]:
        """Kembalikan (diizinkan, detik_tunggu). Mencatat hit bila diizinkan."""
        now = time.monotonic() if now is None else now
        dq = self._hits[kunci]
        batas = now - self.window
        while dq and dq[0] < batas:
            dq.popleft()
        if len(dq) >= self.limit:
            return False, max(self.window - (now - dq[0]), 0.0)
        dq.append(now)
        return True, 0.0

    async def cek_async(self, kunci: str, now: float | None = None) -> tuple[bool, float]:
        return self.cek(kunci, now)


class RedisSlidingWindowLimiter:
    """Sliding window terdistribusi via Redis sorted-set (konsisten lintas worker).

    Best-effort: bila Redis bermasalah, fail-open (mengizinkan) agar tak memblokir layanan.
    Memakai wall-clock (time.time) karena lintas proses. Butuh paket `redis`.
    """

    def __init__(self, redis, limit: int, window: float = 60.0, prefix: str = "ratelimit:") -> None:
        self._r = redis
        self.limit = limit
        self.window = window
        self.prefix = prefix

    async def cek_async(self, kunci: str, now: float | None = None) -> tuple[bool, float]:
        now = time.time() if now is None else now
        k = f"{self.prefix}{kunci}"
        try:
            pipe = self._r.pipeline()
            pipe.zremrangebyscore(k, 0, now - self.window)
            pipe.zcard(k)
            _, jumlah = (await pipe.execute())[:2]
            if jumlah >= self.limit:
                tertua = await self._r.zrange(k, 0, 0, withscores=True)
                retry = (tertua[0][1] + self.window - now) if tertua else self.window
                return False, max(retry, 0.0)
            await self._r.zadd(k, {f"{now}:{os.urandom(4).hex()}": now})
            await self._r.expire(k, int(self.window) + 1)
            return True, 0.0
        except Exception:  # noqa: BLE001 — fail-open bila Redis bermasalah
            return True, 0.0


def buat_limiter(limit: int, window: float = 60.0, settings=None):
    """Factory: limiter Redis bila REDIS_URL diset, selainnya in-memory (T5.1)."""
    if settings is None:
        from config import get_settings
        settings = get_settings()
    if settings.redis_url:
        from redis.asyncio import from_url  # impor malas; hanya saat dipakai
        return RedisSlidingWindowLimiter(from_url(settings.redis_url), limit, window)
    return SlidingWindowLimiter(limit, window)


def klien_key(request: Request) -> str:
    """Identitas klien untuk rate limit: X-Forwarded-For (di balik Nginx) lalu peer."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "tak-dikenal"
