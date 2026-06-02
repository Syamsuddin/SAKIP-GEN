# Changelog

Riwayat perubahan SAKIP-Gen. Format longgar mengikuti *Keep a Changelog*. **Versi 1.0** adalah
rilis publik perdana yang mengonsolidasikan seluruh milestone pengembangan (Fase 0–7) ditambah
refactor perintah terpadu (R1–R5). Penomoran `0.x`/`1.x` di bawah adalah penanda milestone
internal pra-rilis dan dipertahankan sebagai riwayat.

## [1.0] — Rilis perdana — 2026-06-02

Rilis lengkap, *production-ready*, dengan kapabilitas berikut.

### Evaluasi & analitik
- **Evaluasi LKE PermenPAN-RB 88/2021**: model Pengungkit 60 + Hasil 40 — lima komponen berbobot
  (Perencanaan 18, Pengukuran 18, Pelaporan 9, Evaluasi Internal 15, Capaian 40), nilai total,
  predikat **AA–D**. Bobot dikalibrasi dari split AKIP baku 30/30/15/25 dan dapat di-override
  penuh via `LKE_BOBOT`.
- **Analisis gap** berprioritas + estimasi kenaikan nilai per komponen.
- **Peringatan integritas** — deteksi indikator dilabeli *outcome/impact* tetapi rumusannya
  berorientasi *output*.
- **Komponen Hasil dipisah dari Pengukuran**: kelengkapan pengukuran (apakah diukur) berbeda dari
  tingkat capaian aktual (realisasi vs target, di-cap 100%).
- **Analitik lintas**: tren antar-tahun (`/tren`) + benchmark/peringkat antar-OPD (`/benchmark`).

### Siklus SAKIP lengkap
- `/rencana` — perencanaan: sasaran, IKU, tipologi, **keselarasan/cascading pohon kinerja**
  (relasi naik ke Pemda / turun ke unit) dari `sakip_cascading_relasi`.
- `/capaian` — target vs realisasi **per periode** (tahunan/TW1–TW4/semester), indikator berisiko.
- `/laporan` — draft bahan LKjIP (analisis capaian) via LLM, anti-halu (tak mengarang angka).
- `/temuan` — temuan evaluasi internal → rekomendasi → status tindak lanjut.
- `/dokumen` — telusur dokumen SAKIP (RPJMD/Renstra/PK/LKjIP) + versi + jumlah bukti.

### Tata bahasa terpadu & bahasa alami
- **`agent/permintaan.py`** — objek `Permintaan` (aksi × opd × tahun × periode × dokumen × level ×
  fokus) sebagai satu representasi untuk `/slash` **dan** bahasa alami.
- **Dispatcher tunggal** `_jalankan` — semua verba & callback lewat satu jalur (RBAC, resolusi OPD,
  default tahun/periode, peta-error sopan).
- **Penerjemah bahasa alami anti-halu** (`agent/nlu.py`): heuristik deterministik → LLM terstruktur
  (enum tertutup) → *grounding* OPD nyata → eksekusi / **klarifikasi sopan** (nol error teknis ke
  pengguna). LLM tak pernah mengeksekusi/mengarang; `/terapkan` tak bisa via bahasa alami.
- Counter `sakipgen_nlu_total{hasil=heuristik|llm|klarifikasi|tak_paham}`.

### Adapter profil skema (multi-eSAKIP)
- **`db/profiles/`** — `SchemaProfile` (Protocol) + `reference` (skema mainan) + `esakip` (skema
  nyata `db/mysql/schema.sql`), dipilih via `DB_SCHEMA_PROFILE`. Onboarding eSAKIP baru = satu kelas
  profil; kode inti tak berubah. Metode: `bangun_dosir`, `resolve_opd_id`, `daftar_opd`,
  `ambil_temuan`, `ambil_capaian`, `ambil_dokumen`, `ambil_cascading`, `baca_indikator`,
  `terapkan_indikator`.

### Usulan, persetujuan & promosi teraudit
- `agent/improver.py` output→outcome (heuristik + penghalusan LLM Anthropic/Ollama, *fallback* aman).
- Staging `ai_usulan` (`db/staging.py`): draft → disetujui/ditolak; `/usulan` daftar per OPD.
- Mini App (`web/`): token opaque (itsdangerous) + validasi `initData`, form edit, simpan via API.
- `/terapkan` (Kepala Dinas/Admin) → `db/promote.py` dengan **empat pengaman** dalam satu transaksi:
  status `disetujui`, *optimistic lock* (re-hash sumber), *whitelist* kolom, audit sebelum→sesudah
  ke `ai_audit`.

### Telegram & pengalaman pengguna
- **Menu per peran** (`bot/menu.py`): `setMyCommands` per scope — default global + per-chat sesuai
  peran (operator/kepala_dinas/admin), dipasang saat startup & setelah `/daftar`.
- Middleware: throttle (luar) → audit → auth (dalam) → handler.
- Push terjadwal: ringkasan kinerja tiap awal triwulan (1 Jan/Apr/Jul/Okt, 07:00).

### Keamanan, observability & operasional
- Tiga kredensial MySQL *least-privilege* (RO/staging/promotor) — bukan flag aplikasi.
- Auth: allowlist + RBAC; in-memory atau **SQL** (`USE_SQL_AUTH=true`, `db/ddl/auth.sql`);
  admin via `ADMIN_TELEGRAM_IDS`.
- Hardening HTTP: security headers, request-id/access-log, batas ukuran body, perbandingan secret
  webhook konstan-waktu, exception handler generik, `audit_keamanan()` saat startup.
- Rate limit API (`SlidingWindowLimiter`, in-memory/Redis), throttle bot, event log `ai_event`.
- Metrik **Prometheus** di `GET /metrics`; `GET /readyz` mengecek 3 engine DB; `GET /healthz`.
- Deploy satu VPS: systemd (hardening) + gunicorn (`workers=1`) + Nginx/TLS + skrip
  `manage_webhook`/`preflight` + `install.sh` + runbook `deploy/DEPLOY.md`.
- Tooling: `pyproject.toml` (ruff + mypy), GitHub Actions CI, Docker (`Dockerfile`/compose).

### Kualitas
- **101 uji** lulus (SQLite in-memory + ASGI in-process, tanpa MySQL); profil `esakip` diuji dengan
  skema mini kompatibel-SQLite sebagai penjaga *seam-drift*. `ruff` bersih.

---

## Riwayat milestone internal (pra-1.0)

### Fase 7 — Pengerasan produksi & kualitas
- Auth berbasis SQL (`bot/auth_sql.py`, `db/ddl/auth.sql`); sambungan LLM (`agent/llm.py`);
  `/readyz`; `/usulan`; tooling ruff/mypy + CI; Docker.

### Fase 6 — Go-live
- Artefak deploy satu VPS (systemd, gunicorn, Nginx+TLS, `manage_webhook`/`preflight`, installer),
  runbook + checklist, dan dokumentasi `docs/` lengkap.

### Fase 5 — Hardening, observability & audit
- Event log `ai_event` (dwi-sink), `ThrottleMiddleware` + `AuditMiddleware`, security headers +
  request-id + batas body, rate limit API, secret konstan-waktu, `audit_keamanan()`.

### Fase 4 — Penerapan ke tabel sumber
- `terapkan_usulan()` (empat pengaman), engine promotor terpisah + GRANT level kolom,
  `/terapkan` dengan konfirmasi.

### Fase 3 — Usulan, staging & Mini App
- `UsulanPerbaikan` + `hash_indikator`, improver output→outcome, staging `ai_usulan`, Mini App,
  `/usul` + tombol form/Setujui/Tolak.

### Fase 2 — Bot read-only + autentikasi + penjadwal
- `bot/auth.py` (allowlist + RBAC), `/evaluasi`/`/gap`/`/status`, `bot/format.py`, push triwulanan,
  kalibrasi bobot (`LKE_BOBOT`), komponen Hasil, peringatan integritas.

### Fase 1 — Data & evaluasi read-only
- Lapisan data (`db/engines.py`, `db/queries.py`), model Dosir, evaluator LKE, orkestrasi, demo SQLite.

### Fase 0 — Fondasi
- Kerangka FastAPI + bot aiogram (webhook), konfigurasi, healthcheck, mode long-polling dev.
