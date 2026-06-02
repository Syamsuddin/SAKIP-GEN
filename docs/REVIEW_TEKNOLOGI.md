# Review Kematangan Teknologi Stack SAKIP-Gen

> Tinjauan kematangan (maturity), urgensi, efisiensi, integrasi, dan optimasi setiap lapisan
> teknologi dalam sistem. Tanggal review: 2026-06-02.

Sistem ini adalah **monolit FastAPI tunggal** yang melayani healthcheck, webhook Telegram, dan
Mini App, dengan penjadwal in-process — di belakang Nginx+TLS, dijalankan gunicorn 1 worker
melalui systemd. Penilaian per lapisan menggunakan skala bintang (⭐1–5) plus matriks empat
dimensi di akhir.

Skala kematangan:
- ⭐⭐⭐⭐⭐ Matang produksi, praktik baik diterapkan konsisten.
- ⭐⭐⭐⭐ Solid, siap produksi skala kecil-menengah; ada batas yang terdokumentasi.
- ⭐⭐⭐ Fungsional & benar, tapi sederhana / ada celah substansi.
- ⭐⭐ Embrionik / placeholder.

---

## 1. Bot Telegram (aiogram v3) — ⭐⭐⭐⭐

**Stack:** aiogram v3 (webhook produksi + long-polling dev), Dispatcher dengan tiga middleware
berlapis (throttle → audit → auth), dua router (`kinerja` lebih dulu, `base` fallback).

**Kekuatan:**
- Pemilihan aiogram v3 (async, modern) tepat; webhook divalidasi **secret konstan-waktu**
  (`hmac.compare_digest` di [app.py:97](../app.py#L97)) — benar secara keamanan.
- Pemisahan webhook/polling rapi: produksi pakai webhook, [dev_polling.py](../dev_polling.py)
  pakai polling tanpa HTTPS. Lifespan mengatur set/delete webhook otomatis.
- Urutan middleware sengaja dirancang (throttle terluar agar spam ditolak sebelum kerja mahal).

**Batas / risiko:**
- `ThrottleMiddleware` ([bot/throttle.py](../bot/throttle.py)) **in-memory & per-proses** —
  hilang saat restart, dan tidak konsisten bila multi-worker.
- `dp.feed_update` dipanggil **sinkron di dalam request webhook** ([app.py:101](../app.py#L101)):
  Telegram menunggu sampai handler selesai. Untuk handler berat (mis. `/usul` + LLM), ini bisa
  memicu timeout/retry Telegram. Idealnya proses berat dilepas ke background task.

**Urgensi perbaikan:** Sedang (feed_update non-blocking bila beban LLM bertambah).

---

## 2. Web Access Telegram / Mini App — ⭐⭐⭐⭐⭐

**Stack:** FastAPI + Jinja2 (satu template), token opaque itsdangerous, validasi initData
Telegram (HMAC via aiogram), vanilla JS + Telegram WebApp SDK.

Ini **lapisan paling matang** dalam sistem. Alur keamanannya berlapis dan benar
([web/routes.py:59-88](../web/routes.py#L59-L88)):

1. Validasi **initData** (HMAC bot token, [web/security.py:42-50](../web/security.py#L42-L50)) →
   memastikan request benar-benar dari Telegram, bukan dipalsukan.
2. **Token bertanda-tangan & berbatas waktu** (itsdangerous, max_age 1 jam) membawa
   `{usulan_id, telegram_id}` — ID mentah tak pernah di URL.
3. **Cek kepemilikan token** (`tok["t"] == initData.user.id`) → token tak bisa dipakai ulang
   antar-pengguna.
4. **RBAC OPD** (`user.boleh_opd`) + **optimistic lock** via `hash_data_lama` (409 bila data
   berubah) → konsisten dengan pengaman `terapkan_usulan`.

**Kekuatan tambahan:** webview **tidak pernah menyentuh MySQL** (hanya lewat API ber-gerbang);
sukses dicatat ke event log dengan request-id. XSS ditangani via `|e` dan `|tojson` di template.

**Batas:** token fallback ke `webhook_secret` bila `token_secret` kosong
([web/security.py:20-24](../web/security.py#L20-L24)) — fungsional, tapi mencampur tujuan secret;
`audit_keamanan` sudah memperingatkan ini.

**Urgensi perbaikan:** Rendah.

---

## 3. Teknologi AI / LLM — ⭐⭐ (placeholder fungsional)

**Stack:** heuristik aturan sebagai inti; sambungan LLM opsional (Anthropic SDK / Ollama HTTP)
hanya untuk menghaluskan satu field.

**Kekuatan:**
- Desain **provider-agnostic dengan fallback** ([agent/llm.py](../agent/llm.py)): bila tak ada
  API key/host atau panggilan gagal, jatuh ke heuristik — sistem tetap jalan. Tepat untuk
  keandalan.
- Best-effort: semua kegagalan ditelan & dicatat; LLM tak pernah jadi titik gagal kritis.

**Batas / risiko (lihat juga [REVIEW_KECERDASAN.md](REVIEW_KECERDASAN.md)):**
- Peran LLM **sangat dangkal** — hanya merumuskan ulang `uraian`, prompt single-shot tanpa
  few-shot maupun konteks sasaran strategis.
- **Tidak ada caching, retry, circuit breaker, atau pelacakan biaya** untuk panggilan LLM. Tiap
  `/usul` yang menyentuh LLM = panggilan API baru berbayar, tanpa memoisasi hasil identik.
- Model default `claude-3-5-haiku-latest` ([agent/llm.py:40](../agent/llm.py#L40)) — bisa
  dimutakhirkan; pakai skill `claude-api` untuk migrasi & menambah prompt caching.
- Panggilan LLM sinkron dalam alur handler bot (lihat butir #1).

**Urgensi perbaikan:** Sedang–Tinggi (bila LLM hendak jadi nilai jual; saat ini efektif belum
memberi nilai signifikan).

---

## 4. Abstraksi MySQL (SQLAlchemy 2 async) — ⭐⭐⭐⭐

**Stack:** SQLAlchemy 2 async, driver `asyncmy` (produksi) / `aiosqlite` (uji), **tiga engine
terpisah** (RO / staging / promotor) berbasis kredensial least-privilege, SQL `text()` mentah
(tanpa ORM).

**Kekuatan — ini desain arsitektural terkuat sistem:**
- **Pemisahan kewenangan lewat kredensial DB, bukan flag aplikasi**
  ([db/engines.py](../db/engines.py)). RO hanya SELECT; staging tulis `ai_usulan`; promotor punya
  GRANT level-kolom `UPDATE(uraian,satuan,tipologi)`. Defense-in-depth nyata.
- **Engine lazy + overridable** (`set_*_engine`) → Fase 0/1 dan seluruh uji jalan tanpa MySQL,
  cukup inject SQLite. Pola DI yang bersih dan teruji.
- `pool_pre_ping=True` + `pool_recycle=1800` → tahan koneksi MySQL yang di-drop (wait_timeout).
- SQL ditulis **portabel** (stempel waktu ISO-8601 string, nilai turunan dihitung di Python) →
  satu basis kode jalan di SQLite & MySQL.

**Batas / risiko:**
- **Schema seam**: SQL di [db/queries.py](../db/queries.py) & [db/promote.py](../db/promote.py)
  mengasumsikan skema referensi dan **wajib disesuaikan** ke skema SAKIP nyata. Ini titik
  integrasi paling rapuh — salah pemetaan tabel = semua angka salah, senyap.
- **Tanpa ORM & tanpa alat migrasi (Alembic):** DDL berupa berkas `.sql` mentah yang diterapkan
  manual. Untuk tabel turunan `ai_*` masih dapat diterima, tapi evolusi skema rawan drift antar
  lingkungan.
- SQL mentah menambah risiko salah-ketik kolom (tertangkap hanya saat runtime/uji).

**Urgensi perbaikan:** Tinggi untuk schema seam (prasyarat go-live); Rendah untuk Alembic.

---

## 5. Generator HTML / Frontend (Jinja2 + vanilla JS) — ⭐⭐⭐⭐

**Stack:** satu template Jinja2 ([web/templates/usulan.html](../web/templates/usulan.html)),
vanilla JS, variabel tema Telegram (`--tg-theme-*`), tanpa build step.

**Kekuatan:**
- **Tepat-guna**: untuk satu form tinjauan, memilih vanilla JS + satu template (bukan React/Vue)
  adalah keputusan efisiensi yang benar — nol toolchain, nol bundle, muat instan di webview.
- Adaptif tema Telegram (light/dark via CSS variables), `HapticFeedback`, `MainButton`,
  `showConfirm` — integrasi WebApp SDK yang baik.
- Escaping benar (`|e`, `|tojson`) → aman dari XSS injeksi data usulan.
- `TemplateResponse(request, ...)` memakai signature Starlette terbaru (bukan yang deprecated).

**Batas:**
- Form hard-coded untuk tipe `perbaikan_indikator`; tipe usulan lain belum punya UI.
- Tanpa offline/fallback bila SDK Telegram gagal dimuat (mode dimaafkan: memang harus dibuka dari
  Telegram).

**Urgensi perbaikan:** Rendah.

---

## 6. Observability & Audit — ⭐⭐⭐⭐

**Stack:** event log `ai_event` dwi-sink (logger + DB best-effort, [db/events.py](../db/events.py)),
audit perubahan data `ai_audit` ([db/promote.py](../db/promote.py)), request-id + access log
([web/middleware.py](../web/middleware.py)), semua ke journald.

**Kekuatan:**
- **Dua jejak terpisah dengan tujuan jelas**: `ai_event` (siapa-apa-kapan, audit aktivitas) vs
  `ai_audit` (sebelum→sesudah perubahan data sumber). Pemisahan ini matang.
- Dwi-sink best-effort: log selalu tertulis ke journald meski DB belum siap → tak pernah
  kehilangan jejak dan tak pernah jadi titik gagal.
- Request-id menembus dari middleware ke event log → korelasi lintas-lapisan.

**Batas:**
- **Tanpa metrik (Prometheus) maupun tracing terdistribusi** — observability bersifat
  log-sentris. Untuk satu VPS memadai; untuk pertumbuhan, belum ada dashboard kesehatan/limit.
- Tanpa agregasi log terpusat (hanya journald lokal).

**Urgensi perbaikan:** Rendah–Sedang (tambah `/metrics` bila SLA mulai dipantau).

---

## 7. Keamanan & Hardening — ⭐⭐⭐⭐⭐

**Stack:** CSP ketat ramah-Mini-App, security headers, batas ukuran body (413), rate-limit API
sliding-window, perbandingan secret konstan-waktu, RBAC, least-privilege DB, systemd hardening.

**Kekuatan:**
- [web/middleware.py](../web/middleware.py): CSP yang **secara spesifik** mengizinkan
  `telegram.org` + `frame-ancestors` Telegram saja, `X-Content-Type-Options`, `Referrer-Policy`,
  `Permissions-Policy` — konfigurasi yang dipikirkan, bukan default.
- **systemd hardening sangat lengkap** ([deploy/sakip-gen.service](../deploy/sakip-gen.service)):
  `NoNewPrivileges`, `ProtectSystem=full`, `ProtectHome`, `CapabilityBoundingSet=` kosong,
  `RestrictSUIDSGID`, non-root. Ini level produksi serius.
- Nginx meneruskan `X-Forwarded-*` dengan benar (prasyarat rate-limit per-klien akurat),
  `client_max_body_size` selaras `MAX_BODY_BYTES`, webhook dibatasi `POST`.
- `audit_keamanan()` memperingatkan misconfig (secret pendek, non-HTTPS, kode kosong) saat
  startup & preflight.

**Batas:**
- Rate-limit/throttle in-memory (per-proses) → konsisten hanya selama 1 worker.

**Urgensi perbaikan:** Rendah.

---

## 8. Infrastruktur & Deploy — ⭐⭐⭐⭐ (matang, tapi berplafon 1 worker)

**Stack:** gunicorn + UvicornWorker (`workers=1`), Nginx reverse proxy + certbot TLS, systemd
unit, Docker (python:3.12-slim, non-root, healthcheck), docker-compose, skrip `preflight` &
`manage_webhook`, runbook `DEPLOY.md`.

**Kekuatan:**
- Artefak go-live **lengkap dan dewasa**: installer, preflight (cek config + 3 koneksi DB),
  runbook + checklist. Jarang ada proyek sekecil ini selengkap ini.
- Dockerfile higienis: layer cache (`requirements.txt` dulu), non-root uid 10001, healthcheck
  via python (tanpa curl).
- Keputusan `workers=1` **didokumentasikan eksplisit beserta alasan & jalan keluarnya**
  ([deploy/gunicorn.conf.py](../deploy/gunicorn.conf.py)) — ini tanda kematangan rekayasa.

**Batas / risiko utama sistem:**
- **Plafon skala = 1 worker.** Penjadwal in-process + state limiter per-proses memaksa single
  worker. Untuk naik skala perlu: pisahkan scheduler ke service sendiri
  (`ENABLE_SCHEDULER=false` di web) **dan** pindahkan limiter/throttle ke Redis. Sudah dipetakan
  di komentar, tapi belum diimplementasi.
- Tanpa orkestrasi multi-node / HA; satu VPS = satu titik gagal.

**Urgensi perbaikan:** Sedang (hanya relevan saat beban/kebutuhan HA meningkat).

---

## 9. Autentikasi & Manajemen Pengguna — ⭐⭐⭐

**Stack:** allowlist + RBAC (operator/kepala_dinas/admin), dua repo: in-memory (default) & SQL
(`USE_SQL_AUTH=true`, [bot/auth_sql.py](../bot/auth_sql.py)).

**Kekuatan:** abstraksi `AuthRepository` (Protocol) + `set_repo` → mudah ditukar/diuji; SQL repo
portabel (cek-lalu-insert) untuk SQLite & MySQL; kode pendaftaran sekali-pakai.

**Batas:** default produksi masih **in-memory** (hilang saat restart, tidak konsisten
multi-worker) kecuali `USE_SQL_AUTH` diaktifkan. Untuk produksi nyata, SQL auth harus default.

**Urgensi perbaikan:** Sedang (aktifkan `USE_SQL_AUTH` sebelum go-live).

---

## 10. Tooling, Kualitas & CI — ⭐⭐⭐⭐

**Stack:** ruff (E,F,I,UP,B), mypy (longgar: `disallow_untyped_defs=false`), pytest + asyncio
auto-mode, 101 uji (v1.0), GitHub Actions di Py 3.11/3.12.

**Kekuatan:** lint + type-check + uji terintegrasi CI; uji tak butuh MySQL (cepat, deterministik);
struktur uji `test_faseN` memetakan langsung ke perubahan fase.

**Batas:** mypy sengaja longgar (tipe tak wajib) → sebagian manfaat type-safety dilepas; cakupan
uji belum diukur (tanpa coverage gate).

**Urgensi perbaikan:** Rendah.

---

## Matriks empat dimensi

Skala: Tinggi / Sedang / Rendah. **Urgensi** = kebutuhan tindakan; **Efisiensi**, **Integrasi**,
**Optimasi** = tingkat kematangan saat ini (Tinggi = sudah baik).

| Lapisan | Urgensi tindakan | Efisiensi | Integrasi | Optimasi |
|---|---|---|---|---|
| Bot Telegram (aiogram) | Sedang | Tinggi | Tinggi | Sedang (feed_update blocking) |
| Mini App / Web access | Rendah | Tinggi | Tinggi | Tinggi |
| AI / LLM | **Tinggi** | Sedang | **Rendah** (dangkal) | **Rendah** (tanpa cache/retry) |
| Abstraksi MySQL | **Tinggi** (schema seam) | Tinggi | Sedang (seam rapuh) | Tinggi (pool, lazy) |
| Generator HTML | Rendah | Tinggi | Tinggi | Tinggi |
| Observability/Audit | Sedang | Tinggi | Tinggi | Sedang (tanpa metrik) |
| Keamanan/Hardening | Rendah | Tinggi | Tinggi | Tinggi |
| Infra/Deploy | Sedang | Tinggi | Tinggi | Sedang (plafon 1 worker) |
| Auth/Pengguna | Sedang | Tinggi | Sedang | Sedang (default in-memory) |
| Tooling/CI | Rendah | Tinggi | Tinggi | Sedang (mypy longgar) |

---

## Peta jalan teknologi yang disarankan (prioritas)

| Prioritas | Tindakan | Lapisan | Alasan |
|---|---|---|---|
| 🔴 Tinggi | **Sesuaikan & verifikasi schema seam** ke MySQL SAKIP nyata + uji integrasi | MySQL | Prasyarat mutlak go-live; salah pemetaan = salah senyap |
| 🔴 Tinggi | **Aktifkan `USE_SQL_AUTH` sebagai default produksi** | Auth | Hindari kehilangan pengguna saat restart |
| 🟠 Sedang | **Lepas pekerjaan berat (LLM) dari request webhook** ke background task | Bot/AI | Cegah timeout/retry Telegram |
| 🟠 Sedang | **Tambah caching + retry + pelacakan biaya** untuk panggilan LLM; mutakhirkan model + prompt caching (skill `claude-api`) | AI | Efisiensi biaya & kualitas |
| 🟠 Sedang | **Jalur skala-keluar**: scheduler sebagai service terpisah + limiter berbasis Redis, lalu `workers>1` | Infra | Membuka plafon 1-worker bila beban naik |
| 🟢 Rendah | Tambah endpoint `/metrics` (Prometheus) + coverage gate di CI | Observability/CI | Kesiapan operasional jangka panjang |
| 🟢 Rendah | Adopsi Alembic untuk migrasi tabel `ai_*` | MySQL | Cegah drift skema antar lingkungan |

---

## Kesimpulan

Stack SAKIP-Gen **dewasa dan koheren untuk targetnya: satu VPS, beban kecil-menengah, tata kelola
ketat.** Pemilihan teknologi tepat-guna di hampir semua lapisan — async end-to-end, abstraksi DB
tiga-kredensial yang elegan, Mini App yang aman berlapis, dan deploy/hardening setingkat produksi
serius. Kematangan tertinggi ada pada **keamanan, Mini App, dan abstraksi MySQL**; terendah pada
**lapisan AI/LLM**, yang masih placeholder fungsional.

Dua hal yang menentukan kesiapan go-live bukanlah kecanggihan, melainkan **integrasi**:
(1) menyesuaikan *schema seam* ke MySQL SAKIP nyata, dan (2) menjadikan auth SQL sebagai default.
Plafon **1 worker** adalah batas arsitektural yang nyata namun sudah disadari, didokumentasikan,
dan punya jalan keluar yang jelas — sehingga merupakan keputusan rekayasa yang sah, bukan utang
teknis tersembunyi.
