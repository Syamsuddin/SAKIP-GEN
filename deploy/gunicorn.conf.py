"""Konfigurasi Gunicorn untuk SAKIP-Gen (Uvicorn worker).

DEFAULT workers = 1 disengaja. Penjadwal (APScheduler) berjalan in-process dan
rate-limit/throttle bersifat per-proses; menjalankan banyak worker TANPA persiapan
akan menggandakan push terjadwal dan memecah state limiter.

SKALA-KELUAR (T5.1) — untuk WORKERS>1 lakukan SEMUA ini:
  1) Set ENABLE_SCHEDULER=false di web, jalankan `python scheduler_service.py` (satu instans).
  2) Set REDIS_URL agar rate-limit API konsisten lintas worker (web/ratelimit.buat_limiter).
  3) Set USE_SQL_AUTH=true agar daftar pengguna konsisten antar proses.
  4) Set WORKERS=N (mis. 2×CPU+1).
Catatan: throttle bot (bot/throttle.py) tetap per-proses; bot webhook idealnya tetap 1 worker
atau pakai store terpusat untuk throttle juga.
"""
import os

bind = os.getenv("BIND", "127.0.0.1:8000")
workers = int(os.getenv("WORKERS", "1"))
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 60
graceful_timeout = 30
keepalive = 5
loglevel = os.getenv("LOG_LEVEL", "info").lower()
accesslog = "-"          # stdout -> journald
errorlog = "-"
proc_name = "sakip-gen"
forwarded_allow_ips = "127.0.0.1"   # percayai X-Forwarded-* dari Nginx lokal
