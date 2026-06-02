# SAKIP-Gen — Panduan Go-Live (v1.0)

Penyebaran satu VPS Ubuntu: aplikasi FastAPI+aiogram berjalan di `127.0.0.1:8000`
di belakang Nginx (TLS), berdampingan dengan aplikasi web eSAKIP dan MySQL yang sudah ada.

## 1. Prasyarat
- Ubuntu 22.04/24.04, akses sudo.
- Python 3.11+, Nginx, dan MySQL 8 (sudah dipakai aplikasi eSAKIP Anda).
- Subdomain mengarah ke server, mis. `ai.contoh.id` (A/AAAA record).
- Bot Telegram (token dari @BotFather).

## 2. Topologi
```
Telegram  ──HTTPS──>  Nginx (ai.contoh.id:443, TLS)  ──>  127.0.0.1:8000 (gunicorn+UvicornWorker)
                                                            │
                                              MySQL lokal (3 kredensial terpisah)
```

## 3. Pengguna sistem & direktori
```bash
sudo useradd --system --create-home --home-dir /opt/sakip-gen --shell /usr/sbin/nologin sakipgen
sudo rsync -a ./ /opt/sakip-gen/        # salin kode proyek ke /opt/sakip-gen
sudo chown -R sakipgen:sakipgen /opt/sakip-gen
```

## 4. Kode & virtualenv
```bash
sudo -u sakipgen APP_DIR=/opt/sakip-gen bash /opt/sakip-gen/deploy/install.sh
```

## 5. Basis data (least privilege — 3 kredensial)
Terapkan DDL dengan akun MySQL ber-privilege (root/admin). Skema sumber dipetakan oleh **profil
aktif** (`DB_SCHEMA_PROFILE`): profil `esakip` mengikuti `db/mysql/schema.sql` (GRANT siap pakai di
`db/mysql/grants_esakip.sql`), profil `reference` memakai `db/ddl/schema_referensi.sql`. Tabel sumber
SUDAH ADA dari aplikasi eSAKIP Anda.
```bash
mysql sakip < /opt/sakip-gen/db/ddl/staging.sql     # ai_usulan + user sakip_staging
mysql sakip < /opt/sakip-gen/db/ddl/promote.sql     # ai_audit + user sakip_promotor (GRANT kolom)
mysql sakip < /opt/sakip-gen/db/ddl/events.sql      # ai_event + GRANT ke sakip_staging
mysql sakip < /opt/sakip-gen/db/ddl/auth.sql        # bot_users, registration_codes (USE_SQL_AUTH)
# Untuk profil esakip, GRANT 3 kredensial sesuai skema nyata:
#   mysql sakip < /opt/sakip-gen/db/mysql/grants_esakip.sql
# Buat pula user READ-ONLY untuk analitik (bila belum):
#   CREATE USER 'sakip_ro'@'localhost' IDENTIFIED BY '...';
#   GRANT SELECT ON sakip.* TO 'sakip_ro'@'localhost';  (atau batasi ke tabel sumber)
```
Tiga peran kredensial:
- `sakip_ro` — hanya `SELECT` (analitik / penyusunan Dosir / telusur).
- `sakip_staging` — `INSERT/SELECT/UPDATE` pada `ai_usulan`, `INSERT/SELECT` pada `ai_event`.
- `sakip_promotor` — `SELECT` + `UPDATE` **hanya kolom indikator yang diizinkan profil** (esakip:
  `nama,jenis_indikator` pada `sakip_indikator`), `INSERT` audit.

## 6. Konfigurasi `.env`
```bash
sudo -u sakipgen cp /opt/sakip-gen/.env.example /opt/sakip-gen/.env
sudo -u sakipgen nano /opt/sakip-gen/.env
```
Isi minimal untuk produksi:
```
BOT_TOKEN=123456:xxxxxxxx
WEBHOOK_SECRET=<acak panjang >=16>
PUBLIC_BASE_URL=https://ai.contoh.id
TOKEN_SECRET=<acak panjang >=16>
ENV=production
SET_WEBHOOK_ON_STARTUP=true
ENABLE_SCHEDULER=true
USE_SQL_AUTH=true
DB_SCHEMA_PROFILE=esakip
DB_RO_URL=mysql+asyncmy://sakip_ro:...@localhost/sakip
DB_STAGING_URL=mysql+asyncmy://sakip_staging:...@localhost/sakip
DB_PROMOTE_URL=mysql+asyncmy://sakip_promotor:...@localhost/sakip
ADMIN_TELEGRAM_IDS=123456789
REGISTRATION_CODES={"KODE-KADIS":{"nama":"Kepala Dinas","peran":"kepala_dinas","opd_ids":[1]}}
# Opsional LLM (terjemahan niat + rumusan outcome):
# ANTHROPIC_API_KEY=sk-ant-...
# LLM_MODEL=claude-haiku-4-5-20251001
```
Membuat secret acak: `python -c "import secrets;print(secrets.token_urlsafe(24))"`.

## 7. Pra-terbang (preflight)
```bash
cd /opt/sakip-gen && sudo -u sakipgen PYTHONPATH=/opt/sakip-gen .venv/bin/python -m deploy.preflight
```
Pastikan tidak ada item `[!]`/`[-]` kritis (koneksi DB OK, tak ada peringatan keamanan).

## 8. systemd
```bash
sudo cp /opt/sakip-gen/deploy/sakip-gen.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now sakip-gen
systemctl status sakip-gen
journalctl -u sakip-gen -f          # ikuti log
```

## 9. Nginx + TLS
```bash
sudo cp /opt/sakip-gen/deploy/nginx-sakip-gen.conf /etc/nginx/sites-available/sakip-gen
# ganti server_name menjadi domain Anda
sudo ln -s /etc/nginx/sites-available/sakip-gen /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d ai.contoh.id   # menerbitkan & memasang TLS
```

## 10. Webhook Telegram
Bila `SET_WEBHOOK_ON_STARTUP=true`, webhook diset otomatis saat service dimulai
(jalankan service SETELAH Nginx+TLS hidup). Manual / verifikasi:
```bash
cd /opt/sakip-gen && sudo -u sakipgen PYTHONPATH=/opt/sakip-gen .venv/bin/python -m deploy.manage_webhook set
sudo -u sakipgen PYTHONPATH=/opt/sakip-gen .venv/bin/python -m deploy.manage_webhook info
```

## 11. Uji asap (smoke test)
```bash
curl -s https://ai.contoh.id/healthz          # {"status":"ok",...,"version":"1.0.0"}
curl -s https://ai.contoh.id/readyz           # {"ready":true,"checks":{"ro":"ok",...}}
curl -s https://ai.contoh.id/metrics          # counter Prometheus
```
Di Telegram: `/start` → `/daftar KODE-KADIS` → `/nilai 1` (atau "nilai opd 1") → `/gap 1` →
`/capaian 1` → `/rencana 1` → `/usul 1` → buka **form Mini App**, simpan → `/terapkan <id>`
→ konfirmasi.

## 12. Observability
```bash
journalctl -u sakip-gen -f | grep AUDIT      # jejak aktivitas (event log)
curl -s https://ai.contoh.id/metrics         # sakipgen_evaluasi/usulan/penerapan/llm/nlu/error_total
```
Tabel audit: `ai_event` (aktivitas/keamanan), `ai_audit` (perubahan data sumber, sebelum/sesudah).
Pantau pula `/readyz` (kesiapan 3 engine) untuk health-check eksternal.

## 13. Backup
```bash
mysqldump sakip ai_usulan ai_event ai_audit > /var/backups/sakip-gen-$(date +%F).sql
```
Tabel sumber dicadangkan oleh sistem SAKIP utama. Simpan `.env` di tempat aman (berisi secret).

## 14. Update & rollback
```bash
# update
sudo rsync -a ./ /opt/sakip-gen/ && sudo chown -R sakipgen:sakipgen /opt/sakip-gen
sudo -u sakipgen /opt/sakip-gen/.venv/bin/pip install -r /opt/sakip-gen/requirements.txt
sudo systemctl restart sakip-gen
# rollback: pulihkan rilis sebelumnya lalu restart service
```

## 15. Catatan keamanan
- Tiga kredensial MySQL terpisah; promotor hanya boleh `UPDATE` kolom indikator yang diizinkan
  profil aktif (esakip: `nama,jenis_indikator`).
- `audit_keamanan()` mencetak peringatan di log startup bila secret lemah / non-HTTPS /
  tanpa jalur akses / `USE_SQL_AUTH=false`.
- Rate limit API (opsional Redis) + throttle bot aktif. CSP & header keamanan dipasang app.
- Bahasa alami aman: LLM hanya menerjemahkan niat (tak mengarang/mengeksekusi); `/terapkan` tak bisa
  via bahasa alami. Agen tidak pernah menulis tabel sumber; promosi dipicu manusia berwenang.

## 16. Checklist go-live (pre-flight)
- [ ] DNS `ai.contoh.id` mengarah ke server; TLS aktif (certbot).
- [ ] `.env` lengkap; secret kuat (>=16); `ENV=production`; `DB_SCHEMA_PROFILE=esakip`; `USE_SQL_AUTH=true`.
- [ ] 3 user MySQL dibuat dengan GRANT sesuai profil; DDL `staging/promote/events/auth` diterapkan
      (+ `db/mysql/grants_esakip.sql` untuk profil esakip).
- [ ] `python -m deploy.preflight` bersih (DB OK, tanpa peringatan).
- [ ] `systemctl status sakip-gen` aktif; `curl /healthz` & `/readyz` OK.
- [ ] Webhook terpasang; `manage_webhook info` tanpa `last_error_message`.
- [ ] Smoke test bot tuntas: daftar → nilai → capaian → usul → form → terapkan (+ uji bahasa alami).
- [ ] Backup terjadwal untuk `ai_usulan/ai_event/ai_audit` (+ `bot_users/registration_codes`).

## 17. Troubleshooting
- **Webhook `last_error_message` berisi 403** → `WEBHOOK_SECRET` di `.env` tak sama dengan yang diset; jalankan `manage_webhook set` ulang.
- **Bot diam** → `journalctl -u sakip-gen -e`; cek webhook `info`; pastikan Nginx meneruskan `^/webhook/`.
- **429 di Mini App** → rate limit; sesuaikan `API_RATE_PER_MENIT`.
- **Preflight DB GAGAL** → cek DSN `DB_*` & GRANT user; pastikan `asyncmy` terpasang.
- **Push terjadwal dobel** → pastikan `workers=1` (atau pisahkan penjadwal) — lihat `deploy/gunicorn.conf.py`.
