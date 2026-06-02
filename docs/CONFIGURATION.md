# SAKIP-Gen — Konfigurasi (`.env`) v1.0

Dibaca oleh `config.Settings` (pydantic-settings) dari environment / berkas `.env`
(`case_sensitive=false`, `extra=ignore`). Salin dari `.env.example`.

## 1. Variabel
| Variabel | Tipe | Default | Wajib | Keterangan |
|---|---|---|---|---|
| `BOT_TOKEN` | str | — | ya | Token bot Telegram (@BotFather) |
| `WEBHOOK_SECRET` | str | — | ya | Secret path & header webhook (≥16 disarankan) |
| `PUBLIC_BASE_URL` | str | — | ya | URL publik tanpa trailing slash, mis. `https://ai.contoh.id` |
| `SET_WEBHOOK_ON_STARTUP` | bool | `true` | tidak | Set webhook otomatis saat startup |
| `ENABLE_SCHEDULER` | bool | `true` | tidak | Aktifkan push ringkasan triwulanan |
| `LOG_LEVEL` | str | `INFO` | tidak | Level logging (`DEBUG`/`INFO`/…) |
| `ENV` | str | `production` | tidak | `production` mengaktifkan `audit_keamanan` |
| `REGISTRATION_CODES` | str(JSON) | kosong | tidak | `{"KODE":{"nama":..,"peran":..,"opd_ids":[..]}}` (peran ∈ operator/kepala_dinas/admin) |
| `ADMIN_TELEGRAM_IDS` | str(CSV) | kosong | tidak | telegram_id yang otomatis berperan admin (akses tanpa `/daftar`), pemisah `,`/`;` |
| `DB_SCHEMA_PROFILE` | str | `reference` | tidak | Profil skema sumber: `reference` (demo/uji) atau `esakip` (produksi) |
| `DB_RO_URL` | str | kosong | untuk DB | DSN async read-only (`sakip_ro`) |
| `DB_STAGING_URL` | str | kosong | untuk usulan | DSN async staging (`sakip_staging`) |
| `DB_PROMOTE_URL` | str | kosong | untuk `/terapkan` | DSN async promotor (`sakip_promotor`) |
| `MINIAPP_BASE_URL` | str | kosong | tidak | URL form; default `PUBLIC_BASE_URL/usulan` |
| `TOKEN_SECRET` | str | kosong | disarankan | Secret token Mini App (fallback `WEBHOOK_SECRET`) |
| `ANTHROPIC_API_KEY` | str | kosong | opsional | Kunci API Anthropic (terjemahan niat + rumusan outcome) |
| `LLM_MODEL` | str | kosong | opsional | Model LLM, mis. `claude-haiku-4-5-20251001` |
| `OLLAMA_HOST` | str | kosong | opsional | Alternatif LLM lokal (Ollama) |
| `USE_SQL_AUTH` | bool | `false` | produksi | `true` = repo auth berbasis SQL (`db/ddl/auth.sql`), bukan in-memory |
| `API_RATE_PER_MENIT` | int | `30` | tidak | Batas laju `POST /api/usulan/simpan` per klien |
| `BOT_RATE_PER_MENIT` | int | `20` | tidak | Batas laju perintah per pengguna bot |
| `MAX_BODY_BYTES` | int | `65536` | tidak | Batas ukuran body HTTP (→413) |
| `AUDIT_TO_DB` | bool | `true` | tidak | Tulis event log ke DB (selain logger) |
| `REDIS_URL` | str | kosong | tidak | Bila diset, rate-limit API memakai Redis (konsisten lintas worker) |
| `LKE_BOBOT` | str(JSON) | kosong | tidak | Override bobot komponen LKE, mis. `{"Capaian Kinerja":40,"Perencanaan Kinerja":18}` |
| `BIND` | str | `127.0.0.1:8000` | tidak | Dibaca `deploy/gunicorn.conf.py` |

## 2. Properti turunan
- `webhook_path` = `/webhook/<WEBHOOK_SECRET>`
- `webhook_url` = `PUBLIC_BASE_URL` + `webhook_path`

## 3. DSN basis data (async, asyncmy)
```
mysql+asyncmy://<user>:<sandi>@127.0.0.1/sakip
```
Tiga DSN berbeda untuk tiga peran kredensial (lihat `docs/SECURITY.md`).

## 4. Contoh `.env` produksi (minimal)
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
REGISTRATION_CODES={"KADIS-2026":{"nama":"Kepala Dinas","peran":"kepala_dinas","opd_ids":[1]}}
# Opsional LLM (terjemahan niat + rumusan outcome):
ANTHROPIC_API_KEY=sk-ant-...
LLM_MODEL=claude-haiku-4-5-20251001
```

## 5. Tips
- Membuat secret: `python -c "import secrets;print(secrets.token_urlsafe(24))"`.
- Saat menjalankan tanpa MySQL (uji/demo), biarkan `DB_*` kosong, set `DB_SCHEMA_PROFILE=reference`
  (otomatis di uji), dan gunakan SQLite.
- Profil `esakip` mengikuti `db/mysql/schema.sql`; eSAKIP berskema lain perlu profil baru di
  `db/profiles/` (lihat `docs/ARCHITECTURE.md` §5).
- LLM bersifat opsional & aman-gagal: tanpa `ANTHROPIC_API_KEY`/`OLLAMA_HOST`, bahasa alami tetap
  jalan via heuristik dan rumusan usulan tetap dibuat heuristik.
- Bila `OS` mengekspor `ANTHROPIC_API_KEY` lain, jalankan dengan `env -u ANTHROPIC_API_KEY` agar
  nilai `.env` yang dipakai.
- Verifikasi konfigurasi sebelum go-live: `python -m deploy.preflight`.
