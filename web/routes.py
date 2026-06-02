"""Endpoint web/Mini App: form usulan + API simpan (Gerbang) + rate limit + audit.

Alur API simpan: validasi initData -> token sah -> token milik pengguna -> usulan
ada -> RBAC OPD -> data belum basi (409). Dilindungi rate limit per-klien; sukses
dicatat ke event log. Webview TIDAK pernah menyentuh MySQL.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from bot.auth import resolve_user
from config import get_settings
from db.events import catat
from db.staging import ambil_usulan, putuskan_usulan
from web.ratelimit import buat_limiter, klien_key
from web.security import baca_token, validasi_init_data

router = APIRouter(tags=["usulan"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


@lru_cache
def _limiter():
    # Redis bila REDIS_URL diset (konsisten lintas worker), selainnya in-memory.
    return buat_limiter(limit=get_settings().api_rate_per_menit, window=60.0)


async def _rate_limit(request: Request) -> None:
    ok, retry = await _limiter().cek_async(klien_key(request))
    if not ok:
        raise HTTPException(
            status_code=429, detail="Terlalu banyak permintaan.",
            headers={"Retry-After": str(int(retry) + 1)},
        )


@router.get("/usulan", response_class=HTMLResponse)
async def halaman_usulan(request: Request, t: str):
    tok = baca_token(t)
    if tok is None:
        raise HTTPException(status_code=403, detail="Token tidak valid atau kedaluwarsa.")
    u = await ambil_usulan(int(tok["u"]))
    if u is None:
        raise HTTPException(status_code=404, detail="Usulan tidak ditemukan.")
    return templates.TemplateResponse(request, "usulan.html", {"u": u, "token": t})


class SimpanBody(BaseModel):
    initData: str
    token: str
    data: dict


@router.post("/api/usulan/simpan", dependencies=[Depends(_rate_limit)])
async def simpan_usulan(body: SimpanBody, request: Request):
    tid = validasi_init_data(body.initData)
    if tid is None:
        raise HTTPException(status_code=403, detail="Validasi initData gagal.")
    tok = baca_token(body.token)
    if tok is None:
        raise HTTPException(status_code=403, detail="Token tidak valid atau kedaluwarsa.")
    if int(tok["t"]) != int(tid):
        raise HTTPException(status_code=403, detail="Token bukan milik pengguna ini.")
    u = await ambil_usulan(int(tok["u"]))
    if u is None:
        raise HTTPException(status_code=404, detail="Usulan tidak ditemukan.")
    user = await resolve_user(tid)
    if user is None or not user.boleh_opd(u.opd_id):
        raise HTTPException(status_code=403, detail="Anda tidak berwenang atas OPD ini.")
    if str(body.data.get("hash_data_lama")) != str(u.hash_data_lama):
        raise HTTPException(status_code=409, detail="Data sumber telah berubah; muat ulang lalu tinjau kembali.")
    ok = await putuskan_usulan(
        u.id, ditinjau_oleh=user.nama, status="disetujui",
        perubahan=body.data.get("perubahan"), alasan=body.data.get("alasan"),
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Usulan tidak ditemukan.")
    await catat(
        "usulan", "setujui_form", telegram_id=tid, nama=user.nama, peran=user.peran,
        opd_id=u.opd_id, ringkas=f"usulan #{u.id} {u.indikator_id}",
        request_id=getattr(request.state, "request_id", None),
    )
    return {"ok": True, "usulan_id": u.id, "status": "disetujui"}
