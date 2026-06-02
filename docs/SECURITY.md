# SAKIP-Gen — Model Keamanan (v1.0)

## 1. Prinsip
Integritas data SAKIP adalah prioritas. Agen **hanya membaca** sumber; semua tulisan melewati
staging yang disetujui manusia; promosi ke sumber dipicu manusia berwenang dan teraudit. Telegram
hanya pemicu; kebenaran & audit ada di server.

## 2. RBAC
`User(telegram_id, nama, peran, opd_ids)` dengan `peran ∈ {operator, kepala_dinas, admin}`.
- `is_admin` → akses semua OPD.
- `boleh_opd(opd_id)` → admin, atau `opd_id` ada di `opd_ids`.
- `boleh_promosi()` → `peran ∈ {kepala_dinas, admin}` (syarat `/terapkan`).

Pendaftaran via **kode sekali-pakai** (`REGISTRATION_CODES`), mengikat `telegram_id` ke identitas
+ peran + daftar OPD. `ADMIN_TELEGRAM_IDS` memberi peran **admin** otomatis (akses bot tanpa
`/daftar`). Repo pengguna **in-memory** (default) atau **berbasis SQL** (`USE_SQL_AUTH=true`,
`db/ddl/auth.sql`) untuk produksi. `AuthMiddleware` memblokir non-publik bagi yang belum terdaftar.

## 3. Least privilege — tiga kredensial MySQL
| Kredensial | GRANT |
|---|---|
| `sakip_ro` | `SELECT` (tabel sumber / skema) |
| `sakip_staging` | `INSERT,SELECT,UPDATE` `ai_usulan`; `INSERT,SELECT` `ai_event` |
| `sakip_promotor` | `SELECT` + `UPDATE` **hanya kolom indikator yang diizinkan profil aktif**; `SELECT(...),UPDATE(status,diterapkan_oleh,diterapkan_pada)` `ai_usulan`; `INSERT,SELECT` `ai_audit` |

Kolom yang dapat dipromosikan ditentukan oleh `kolom_diizinkan` profil aktif: profil `reference`
= `{uraian, satuan, tipologi}` pada `indikator`; profil `esakip` = `{uraian→nama,
tipologi→jenis_indikator}` pada `sakip_indikator` (`satuan` FK belum dipromosikan). Promotor
**tidak bisa** menyentuh kolom/tabel di luar daftar tersebut — dijamin oleh GRANT level kolom
(`db/mysql/grants_esakip.sql` untuk produksi), bukan sekadar kode. DDL tabel agen di
`db/ddl/staging.sql`, `promote.sql`, `events.sql`, `auth.sql`.

## 4. Gerbang Mini App (defense-in-depth)
`POST /api/usulan/simpan` menegakkan berlapis: **(1)** validasi HMAC `initData` Telegram →
identitas asli; **(2)** token opaque bertanda tangan + berbatas waktu (itsdangerous); **(3)**
token harus milik pengirim; **(4)** RBAC OPD; **(5)** optimistic lock (`hash_data_lama`).
URL form membawa **token**, bukan ID mentah.

## 5. Hardening
- **Security headers** (`web/middleware.py`): CSP ramah-Telegram (`frame-ancestors` web.telegram.org),
  `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Permissions-Policy`.
- **Bahasa alami aman**: penerjemah NL (`agent/nlu.py`) memakai enum aksi tertutup; LLM hanya
  menerjemahkan niat (tak mengeksekusi, tak mengarang data). Aksi destruktif (`/terapkan`) **tidak**
  dapat dipicu lewat bahasa alami. Semua galat ditelan jadi pesan ramah — **nol error teknis** ke
  pengguna (detail hanya ke log + counter).
- **Rate limit API** (`web/ratelimit.py`): sliding-window per klien (`X-Forwarded-For` di balik
  Nginx) → 429 + `Retry-After`; opsional **Redis** (`REDIS_URL`) untuk konsistensi lintas worker.
- **Throttle bot** (`bot/throttle.py`): batasi laju per `telegram_id`.
- **Webhook**: perbandingan secret **konstan-waktu** (`hmac.compare_digest`); di Nginx dibatasi `POST`.
- **Batas ukuran body** (413) berbasis header, tanpa membaca stream.
- **Exception handler generik**: tidak membocorkan stack trace; balas 500 ringkas + `request_id`.
- **systemd hardening**: `NoNewPrivileges`, `ProtectSystem`, `PrivateTmp`, `ProtectHome`, dll.

## 6. Audit (dua lapis, saling melengkapi)
- **`ai_event`** (`db/events.py`) — **aktivitas/keamanan**: siapa/apa/kapan/hasil. Dwi-sink:
  **selalu** ke logger (stdout→journald) + **best-effort** ke DB. `AuditMiddleware` mencatat tiap
  perintah/callback; route web mencatat persetujuan via form.
- **`ai_audit`** (`db/promote.py`) — **perubahan data sumber**: `data_sebelum`/`data_sesudah`,
  oleh siapa, kapan, untuk tiap penerapan `/terapkan`.

`audit_keamanan(settings)` (di `app.py` saat startup) mencetak **peringatan** (non-fatal) bila di
`ENV=production` ditemukan: `WEBHOOK_SECRET` < 16 karakter, `TOKEN_SECRET` lemah/kosong,
`PUBLIC_BASE_URL` bukan HTTPS, `REGISTRATION_CODES` **dan** `ADMIN_TELEGRAM_IDS` kosong (tak ada
jalur akses), atau `USE_SQL_AUTH=false` (auth in-memory hilang saat restart). **Selalu periksa log
startup.**

## 7. Minimisasi data & UU ITE
Hindari mendorong data pribadi sensitif (mis. NIK, SKP individu) melalui Telegram. Usulan
berfokus pada metadata indikator (uraian/satuan/tipologi). Pertimbangkan kewajiban hukum
(UU ITE/PDP) sebelum memperluas cakupan data yang dikirim ke klien.

## 8. Praktik operasional
- Simpan `.env` (berisi secret) dengan izin ketat; jangan commit ke VCS (`.gitignore`).
- Buat `WEBHOOK_SECRET` & `TOKEN_SECRET` acak ≥ 24 karakter:
  `python -c "import secrets;print(secrets.token_urlsafe(24))"`.
- Batasi exposure: aplikasi hanya `127.0.0.1:8000`; publik hanya lewat Nginx+TLS.
- Cadangkan `ai_usulan`, `ai_event`, `ai_audit` secara berkala.

## 9. Catatan & batas
- Throttle bot & penjadwal **per-proses** (cocok satu worker); rate-limit API dapat memakai Redis
  (`REDIS_URL`) untuk konsistensi lintas worker.
- CSP `frame-ancestors` melindungi embed web; webview native Telegram umumnya tidak menegakkan CSP
  — anggap lapisan tambahan.
- Repo auth in-memory default; gunakan `USE_SQL_AUTH=true` untuk produksi nyata.
