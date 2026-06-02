#!/usr/bin/env bash
# Pemasangan SAKIP-Gen di Ubuntu (idempoten & konservatif).
# TIDAK menyentuh MySQL/Nginx secara destruktif — langkah itu manual (lihat DEPLOY.md).
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/sakip-gen}"
PY="${PY:-python3}"

echo "==> Virtualenv di ${APP_DIR}/.venv"
"${PY}" -m venv "${APP_DIR}/.venv"
"${APP_DIR}/.venv/bin/pip" install --upgrade pip wheel

echo "==> Memasang dependensi produksi"
"${APP_DIR}/.venv/bin/pip" install -r "${APP_DIR}/requirements.txt"

echo "==> Memeriksa .env"
if [ ! -f "${APP_DIR}/.env" ]; then
  echo "    .env belum ada -> 'cp .env.example .env' lalu isi nilainya."
fi

echo "==> Selesai. Lanjut: terapkan DDL, pasang systemd & Nginx (lihat deploy/DEPLOY.md)."
echo "    Pra-terbang: PYTHONPATH=${APP_DIR} ${APP_DIR}/.venv/bin/python -m deploy.preflight"
