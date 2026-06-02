# SAKIP-Gen — Panduan Instalasi (v1.0)

Dokumen ini mencakup **tiga jalur instalasi**: (A) lokal/pengembangan, (B) Docker, dan
(C) produksi di VPS. Untuk runbook go-live produksi yang mendetail (systemd, Nginx, TLS, checklist),
lihat [`deploy/DEPLOY.md`](deploy/DEPLOY.md). Untuk referensi variabel konfigurasi, lihat
[`docs/CONFIGURATION.md`](docs/CONFIGURATION.md).

## Daftar Isi
- [Prasyarat](#prasyarat)
- [Memperoleh Kode](#memperoleh-kode)
- [Jalur A — Lokal / Pengembangan](#jalur-a--lokal--pengembangan)
- [Jalur B — Docker](#jalur-b--docker)
- [Jalur C — Produksi (VPS Ubuntu)](#jalur-c--produksi-vps-ubuntu)
- [Basis Data dan Kredensial](#basis-data-dan-kredensial)
- [Verifikasi Pasca-Instalasi](#verifikasi-pasca-instalasi)
- [Mengaktifkan Fitur Opsional](#mengaktifkan-fitur-opsional)
- [Pembaruan (Upgrade)](#pembaruan-upgrade)
- [Uninstall](#uninstall)
- [Pemecahan Masalah Instalasi](#pemecahan-masalah-instalasi)

## Prasyarat
- **Python 3.11+** (3.12 disarankan).
- Bot Telegram + token dari [@BotFather](https://t.me/BotFather).
- **Produksi:** MySQL 8 (yang dipakai aplikasi SAKIP Anda), Nginx, dan domain/subdomain ber-HTTPS.
- **Opsional:** Docker & Docker Compose; kunci Anthropic API atau server Ollama (untuk fitur LLM).

## Memperoleh Kode
```bash
tar -xzf sakip-gen-v1.0.tar.gz
cd sakip-gen
```

## Jalur A — Lokal / Pengembangan
Cocok untuk mencoba, mengembangkan, dan menjalankan pengujian (tanpa MySQL).
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# Verifikasi
ruff check .            # lint bersih
python -m pytest -q     # 101 passed

# Demo evaluasi TANPA MySQL (SQLite in-memory)
python demo_evaluasi.py
```
Menjalankan bot lokal (mode long-polling, tanpa HTTPS):
```bash
cp .env.example .env
# Isi minimal: BOT_TOKEN, WEBHOOK_SECRET, PUBLIC_BASE_URL (boleh placeholder untuk polling)
python dev_polling.py
```

## Jalur B — Docker
```bash
cp .env.example .env        # isi nilai (lihat docs/CONFIGURATION.md)
docker compose up -d --build
docker compose logs -f sakip-gen
curl -s http://127.0.0.1:8000/healthz
```
Catatan:
- Di dalam container aplikasi mendengarkan `0.0.0.0:8000` (variabel `BIND`); port dipetakan **hanya**
  ke `127.0.0.1:8000` di host.
- MySQL diasumsikan **eksternal**; arahkan `DB_*_URL` ke host (mis. IP host / `host.docker.internal`).
- **Webhook tetap memerlukan HTTPS**: terminasikan TLS di Nginx host dan teruskan ke `127.0.0.1:8000`
  (lihat blok Nginx pada `deploy/DEPLOY.md`). Atau pakai mode polling untuk uji internal.

## Jalur C — Produksi (VPS Ubuntu)
Ringkasan; detail systemd/Nginx/TLS ada di [`deploy/DEPLOY.md`](deploy/DEPLOY.md).

### C.1 Pengguna sistem & salin kode
```bash
sudo useradd --system --create-home --home-dir /opt/sakip-gen --shell /usr/sbin/nologin sakipgen
sudo rsync -a ./ /opt/sakip-gen/
sudo chown -R sakipgen:sakipgen /opt/sakip-gen
```
### C.2 Virtualenv & dependensi
```bash
sudo -u sakipgen APP_DIR=/opt/sakip-gen bash /opt/sakip-gen/deploy/install.sh
```
### C.3 Basis data & kredensial
Lihat bagian [Basis Data dan Kredensial](#basis-data-dan-kredensial).
### C.4 Konfigurasi `.env` (produksi)
```bash
sudo -u sakipgen cp /opt/sakip-gen/.env.example /opt/sakip-gen/.env
sudo -u sakipgen nano /opt/sakip-gen/.env
```
Nilai produksi yang umum:
```
BOT_TOKEN=123456:xxxxxxxx
WEBHOOK_SECRET=<token_urlsafe(24)>
PUBLIC_BASE_URL=https://ai.contoh.id
TOKEN_SECRET=<token_urlsafe(24)>
ENV=production
SET_WEBHOOK_ON_STARTUP=true
ENABLE_SCHEDULER=true
USE_SQL_AUTH=true
DB_SCHEMA_PROFILE=esakip
DB_RO_URL=mysql+asyncmy://sakip_ro:***@127.0.0.1/sakip
DB_STAGING_URL=mysql+asyncmy://sakip_staging:***@127.0.0.1/sakip
DB_PROMOTE_URL=mysql+asyncmy://sakip_promotor:***@127.0.0.1/sakip
ADMIN_TELEGRAM_IDS=123456789
# LLM opsional (terjemahan niat + rumusan outcome):
# ANTHROPIC_API_KEY=...
# LLM_MODEL=claude-haiku-4-5-20251001
```
> Jika `USE_SQL_AUTH=true`, kode pendaftaran dibaca dari **tabel** `registration_codes`
> (variabel `REGISTRATION_CODES` diabaikan). Jika `false`, isi `REGISTRATION_CODES` (JSON) di `.env`.

Membuat secret acak: `python -c "import secrets;print(secrets.token_urlsafe(24))"`.

### C.5 Pra-terbang, layanan, proxy, webhook
```bash
cd /opt/sakip-gen
sudo -u sakipgen PYTHONPATH=/opt/sakip-gen .venv/bin/python -m deploy.preflight   # cek config + DB
```
Lalu pasang systemd, Nginx + `certbot`, dan set webhook sesuai
[`deploy/DEPLOY.md`](deploy/DEPLOY.md) bagian 8–10.

## Basis Data dan Kredensial
Terapkan DDL memakai akun MySQL ber-privilege (root/admin). Skema **sumber** dipetakan oleh
**profil aktif** (`DB_SCHEMA_PROFILE`): profil `esakip` mengikuti `db/mysql/schema.sql` (eSAKIP
nyata; lihat juga `db/mysql/seed.sql` & `db/mysql/grants_esakip.sql`), profil `reference` memakai
`db/ddl/schema_referensi.sql` (demo/uji). eSAKIP berskema berbeda perlu profil baru di
`db/profiles/` (lihat `docs/ARCHITECTURE.md` §5). Tabel sumber **sudah ada** dari aplikasi Anda.
```bash
mysql sakip < db/ddl/staging.sql     # ai_usulan + user sakip_staging
mysql sakip < db/ddl/promote.sql     # ai_audit + user sakip_promotor (GRANT kolom)
mysql sakip < db/ddl/events.sql      # ai_event + GRANT ke sakip_staging
mysql sakip < db/ddl/auth.sql        # bot_users, registration_codes (bila USE_SQL_AUTH=true)
```
Buat akun **read-only** untuk analitik:
```sql
CREATE USER 'sakip_ro'@'localhost' IDENTIFIED BY 'GANTI_SANDI_KUAT';
GRANT SELECT ON sakip.* TO 'sakip_ro'@'localhost';   -- atau batasi ke tabel sumber
FLUSH PRIVILEGES;
```
Empat peran kredensial:
| Kredensial | Hak |
|---|---|
| `sakip_ro` | `SELECT` (analitik / penyusunan Dosir) |
| `sakip_staging` | `INSERT/SELECT/UPDATE` `ai_usulan`; `INSERT/SELECT` `ai_event`; kelola `bot_users`/`registration_codes` |
| `sakip_promotor` | `SELECT` + `UPDATE` kolom indikator yang diizinkan profil (esakip: `nama,jenis_indikator` pada `sakip_indikator`); `INSERT` `ai_audit` |

Menerbitkan kode pendaftaran (mode auth SQL):
```sql
INSERT INTO registration_codes (kode, nama, peran, opd_ids)
VALUES ('KADIS-2026', 'Kepala Dinas', 'kepala_dinas', JSON_ARRAY(1));
```

## Verifikasi Pasca-Instalasi
```bash
curl -s https://ai.contoh.id/healthz   # {"status":"ok",...,"version":"1.0.0"}
curl -s https://ai.contoh.id/readyz    # {"ready":true,"checks":{"ro":"ok",...}}
curl -s https://ai.contoh.id/metrics   # counter Prometheus
```
Di Telegram: `/start` → `/daftar <kode>` → `/nilai 1` (atau tulis "nilai opd 1"). (Di lingkungan
dev: `ruff check .` dan `python -m pytest -q`.)

## Mengaktifkan Fitur Opsional
- **Profil skema produksi:** set `DB_SCHEMA_PROFILE=esakip` (default `reference` untuk demo/uji).
- **Auth berbasis SQL:** set `USE_SQL_AUTH=true`, terapkan `db/ddl/auth.sql`, terbitkan kode di tabel.
- **LLM (terjemahan bahasa alami + rumusan outcome):** isi `ANTHROPIC_API_KEY` (atau `OLLAMA_HOST`)
  dan `LLM_MODEL`. Bila gagal/tak diisi, bahasa alami tetap jalan via heuristik dan usulan tetap
  dibuat heuristik (aman-gagal).
- **Rate limit lintas worker:** set `REDIS_URL` (default in-memory, cocok 1 worker).

## Pembaruan (Upgrade)
```bash
# 1) Cadangkan tabel agen
mysqldump sakip ai_usulan ai_event ai_audit bot_users registration_codes > backup-$(date +%F).sql
# 2) Perbarui kode & dependensi
sudo rsync -a ./ /opt/sakip-gen/ && sudo chown -R sakipgen:sakipgen /opt/sakip-gen
sudo -u sakipgen /opt/sakip-gen/.venv/bin/pip install -r /opt/sakip-gen/requirements.txt
# 3) Terapkan DDL baru bila ada perubahan skema, lalu restart
sudo systemctl restart sakip-gen
```
Rollback: pulihkan rilis sebelumnya lalu `systemctl restart sakip-gen`.

## Uninstall
```bash
sudo systemctl disable --now sakip-gen
sudo rm /etc/systemd/system/sakip-gen.service && sudo systemctl daemon-reload
# hapus webhook
cd /opt/sakip-gen && sudo -u sakipgen PYTHONPATH=/opt/sakip-gen .venv/bin/python -m deploy.manage_webhook delete
sudo rm -rf /opt/sakip-gen
# (opsional) hapus blok Nginx + sertifikat, drop user MySQL & tabel ai_*/bot_users/registration_codes
```

## Pemecahan Masalah Instalasi
| Gejala | Solusi |
|---|---|
| `pip install asyncmy` gagal dikompilasi | Pastikan wheel tersedia untuk platform Anda; atau pasang toolchain (`build-essential`, header MySQL); alternatif paling mudah: pakai **Docker**. |
| `RuntimeError: DB_*_URL belum diset` | Isi DSN terkait di `.env` (lihat `docs/CONFIGURATION.md`). |
| `/readyz` mengembalikan 503 | Periksa DSN & GRANT; jalankan `python -m deploy.preflight`. |
| Webhook `last_error_message` berisi 403 | `WEBHOOK_SECRET` tak sama dengan yang diset; jalankan ulang `manage_webhook set`. |
| Port 8000 sudah dipakai | Ubah `BIND` (mis. `127.0.0.1:8010`) dan sesuaikan Nginx/compose. |
| `USE_SQL_AUTH=true` tetapi pendaftaran gagal | Pastikan `db/ddl/auth.sql` sudah diterapkan dan kode ada di `registration_codes`. |
| Bot diam | `journalctl -u sakip-gen -e`; cek `manage_webhook info`; pastikan Nginx meneruskan `^/webhook/`. |
