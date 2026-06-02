"""Middleware HTTP (Fase 5): security headers + konteks/akses-log + batas ukuran body."""
from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("sakip-gen.http")

# CSP kompatibel dengan Telegram Mini App (skrip telegram.org; embed dari Telegram web).
_CSP = (
    "default-src 'self'; "
    "script-src 'self' https://telegram.org; "
    "style-src 'self' 'unsafe-inline'; "
    "connect-src 'self'; "
    "img-src 'self' data:; "
    "base-uri 'none'; "
    "frame-ancestors https://web.telegram.org https://telegram.org"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers.setdefault("Content-Security-Policy", _CSP)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        return response


class RequestContextMiddleware(BaseHTTPMiddleware):
    """ID permintaan + access log (metode, path, status, durasi) + batas ukuran body."""

    def __init__(self, app, max_body_bytes: int = 65536) -> None:
        super().__init__(app)
        self.max_body_bytes = max_body_bytes

    async def dispatch(self, request: Request, call_next):
        cl = request.headers.get("content-length")
        if cl and cl.isdigit() and int(cl) > self.max_body_bytes:
            return JSONResponse({"detail": "Payload terlalu besar."}, status_code=413)

        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        request.state.request_id = rid
        t0 = time.monotonic()
        try:
            response = await call_next(request)
        except Exception:
            dur = (time.monotonic() - t0) * 1000
            logger.exception("HTTP %s %s gagal (rid=%s, %.1fms)",
                             request.method, request.url.path, rid, dur)
            raise
        dur = (time.monotonic() - t0) * 1000
        response.headers["X-Request-ID"] = rid
        logger.info("HTTP %s %s -> %s (rid=%s, %.1fms)",
                    request.method, request.url.path, response.status_code, rid, dur)
        return response
