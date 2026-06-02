"""Pra-terbang (preflight) sebelum go-live: cek konfigurasi & koneksi DB (best-effort).

  python -m deploy.preflight

Keluar dengan kode != 0 bila konfigurasi wajib hilang.
"""
from __future__ import annotations

import asyncio

from sqlalchemy import text

from config import audit_keamanan, get_settings
from db.engines import get_promote_engine, get_ro_engine, get_staging_engine


async def _cek_db(nama: str, getter) -> bool:
    try:
        engine = getter()
    except Exception as e:  # noqa: BLE001
        print(f"  [-] {nama}: tidak dikonfigurasi ({e})")
        return False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print(f"  [OK] {nama}: terhubung")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"  [!] {nama}: GAGAL terhubung ({e})")
        return False


async def main() -> int:
    try:
        s = get_settings()
    except Exception as e:  # noqa: BLE001
        print("KONFIGURASI WAJIB HILANG:", e)
        return 2

    print("Konfigurasi inti:")
    print("  env             :", s.env)
    print("  webhook_url     :", s.webhook_url)
    print("  set webhook     :", s.set_webhook_on_startup)
    print("  scheduler aktif :", s.enable_scheduler)

    print("Peringatan keamanan:")
    peringatan = audit_keamanan(s)
    if peringatan:
        for x in peringatan:
            print("  [!]", x)
    else:
        print("  (tidak ada)")

    print("Koneksi basis data (best-effort):")
    await _cek_db("read-only", get_ro_engine)
    await _cek_db("staging  ", get_staging_engine)
    await _cek_db("promotor ", get_promote_engine)

    print("\nPreflight selesai. Tinjau item [!]/[-] sebelum go-live.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
