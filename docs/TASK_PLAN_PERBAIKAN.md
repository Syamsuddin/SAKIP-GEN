# Rencana Perbaikan Terintegrasi SAKIP-Gen

> Sintesis empat review menjadi satu rencana kerja berfase, lengkap dengan keterlacakan
> (traceability) ke setiap temuan, dependensi antar-tugas, kriteria selesai, dan estimasi.
> Tanggal: 2026-06-02.

Sumber yang diintegrasikan:
- [REVIEW_KECERDASAN.md](REVIEW_KECERDASAN.md) — kode `KEC`
- [REVIEW_TEKNOLOGI.md](REVIEW_TEKNOLOGI.md) — kode `TEK`
- [REVIEW_ABSTRAKSI_DATA.md](REVIEW_ABSTRAKSI_DATA.md) — kode `DAT`
- [REVIEW_SAKIP_BISNIS.md](REVIEW_SAKIP_BISNIS.md) — kode `BIS`

## Status implementasi (per 2026-06-02)

| Tugas | Status | Catatan |
|---|---|---|
| T0.1 Disclaimer output | ✅ Selesai | `bot/format.py` (+ template Mini App, demo). Uji di `test_fase2`. |
| T0.2 Reposisi label | ✅ Selesai | "Indeks Kualitas Implementasi SAKIP (proses)"; predikat "(indikatif)". |
| T1.1 Adaptasi schema seam | ✅ Selesai (arsitektur adaptif) | Diganti pendekatan **schema-profile** (`db/profiles/`): profil `reference` (demo/uji) + `esakip` (skema nyata `db/mysql/schema.sql`), dipilih via `DB_SCHEMA_PROFILE`. `queries.py`/`promote.py` mendelegasi ke profil aktif. Uji: `test_seam_konsistensi_baca_tulis` (reference) + `test_profil_esakip` (baca+promosi pada skema eSAKIP). GRANT esakip: `db/mysql/grants_esakip.sql`. Onboarding eSAKIP lain = tulis 1 profil. |
| T1.2 Keamanan auth produksi | ✅ Selesai | Peringatan `audit_keamanan` saat `production` + in-memory; uji di `test_fase5`. (SQL repo aktif via `USE_SQL_AUTH=true`.) |
| T1.3 Satu koneksi RO | ✅ Selesai | `bangun_dosir` berbagi satu koneksi; `db/queries.py` mypy-bersih. |

| T2.1 Capaian aktual ke skor | ✅ Selesai | Komponen **Capaian Kinerja** (Hasil) memakai `persen_capaian` (cap 100%). Pengukuran tetap menilai KELENGKAPAN proses (pemisahan benar). Uji: `test_validitas_nilai`. |
| T2.2 Komponen Hasil | ✅ Selesai (capaian) | Ditambahkan komponen Hasil = Capaian Kinerja (bobot 40). Akuntabilitas keuangan (`anggaran_*`) menyusul. |
| T2.3 Kalibrasi bobot | ✅ Selesai (bobot konfigurabel) | Bobot default Pengungkit 60 + Hasil 40 di `BOBOT_DEFAULT`; override via `LKE_BOBOT` (JSON) / arg `evaluasi_lke(bobot=...)`. Granularitas sub-aspek (Pemenuhan/Kualitas/Pemanfaatan) per komponen = penyempurnaan lanjut. |
| T2.4 Anti-gaming | ✅ Selesai (mislabel) | `HasilEvaluasi.peringatan` menandai indikator berlabel outcome tapi rumusan berbau output; tampil di bot & demo. Verifikasi bukti flag = lanjutan. |

| T3.1 Lepas LLM dari webhook | ✅ Selesai | `/usul` balas cepat (draft heuristik), penghalusan LLM di `asyncio.create_task` lalu edit pesan + `db.staging.perbarui_draft`. |
| T3.2 Caching/retry/biaya LLM | ✅ Selesai | Memoisasi respons + circuit breaker + log token; retry/timeout via SDK Anthropic. Model `claude-haiku-4-5`. Prompt caching Anthropic dilewati (prefix < ambang Haiku 4096 — didokumentasikan). Uji: `test_fase3_llm`. |
| T3.3 Prompt diperkaya | ✅ Selesai | Few-shot output→outcome + konteks sasaran strategis + satuan (`agent/llm._prompt`, `sempurnakan_dengan_llm(sasaran=,satuan=)`). |
| T3.4 Deteksi mislabel LLM | ✅ Selesai | `deteksi_mislabel_llm()` (verifikasi semantik tipologi, fallback None → heuristik T2.4). Terverifikasi live. Wiring ke peringatan evaluator = opsional lanjutan. |
| T3.5 Perluas drafting | 🟡 Sebagian (advisory) | `saran_lanjutan()` memberi rekomendasi pengukuran/pelaporan/evaluasi/capaian, tampil di `/gap`. Usulan TERSTRUKTUR auto-apply untuk tipe non-indikator = lanjutan (perlu desain model+promote+UI). |

| T4.1 SQLAlchemy Core MetaData | ✅ Selesai (kanonik + drift-guard) | `db/schema.py` mendefinisikan tabel `ai_*`/auth kanonik; uji `test_drift_skema_agen` menjaga selaras dgn `*_SCHEMA_SQLITE`. Adopsi Core di SQL query = lanjutan. |
| T4.2 Status sumber-tunggal | ✅ Selesai | Invarian didokumentasikan di `db/staging.py`; uji `test_status_invarian_kolom_otoritatif` (kolom otoritatif). |
| T4.3 Alembic migrasi `ai_*` | ✅ Selesai | `alembic/` + migrasi `0001_initial` dari `db/schema.metadata`; `alembic upgrade head` terverifikasi di SQLite & di CI. Tabel sumber di luar kendali migrasi. |
| T4.4 /metrics + coverage gate | ✅ Selesai | `metrics.py` (Prometheus teks, tanpa dependensi) + `/metrics`; counter evaluasi/usulan/penerapan/llm/error. CI `.github/workflows/ci.yml` (ruff + pytest `--cov-fail-under=65` + alembic). |

| T5.1 Jalur skala-keluar | ✅ Selesai (Redis perlu server utk diuji) | `scheduler_service.py` (penjadwal mandiri); `WORKERS` env di gunicorn conf + runbook; `web/ratelimit.buat_limiter()` → Redis bila `REDIS_URL` (in-memory default). Uji factory + `cek_async`. Throttle bot tetap per-proses (didokumentasikan). |
| T5.2 Tren & benchmark | ✅ Selesai | `agent/analitik.delta_nilai/tren_opd` + `peringkat/benchmark_opd`; perintah bot `/tren` & `/benchmark`. Uji logika murni. |
| T5.3 Cascading/keselarasan | 🟡 Sebagian | `keselarasan_sasaran()` menandai sasaran tanpa indikator outcome/impact; tampil di push triwulanan. Cascading vertikal lintas-dokumen (RPJMD→Renstra→PK, `sakip_cascading_relasi`) menyusul (perlu perluasan model Dosir). |
| T5.4 Monitoring berisiko | ✅ Selesai | `indikator_berisiko()` (capaian < ambang) + keselarasan tampil di push triwulanan (`bot/scheduler._bagian_dini`). Uji `test_bagian_dini_push`. |

**Status fase:** Fase 0–2 & 4 ✅ penuh · Fase 1 ✅ (adaptif) · Fase 3 ✅ inti (+1 advisory partial) · Fase 5 ✅ (T5.3 partial; Redis butuh server untuk uji end-to-end).

---

## 1. Sintesis: gambaran terintegrasi

Membaca keempat review sebagai satu kesatuan, muncul **satu ketegangan sentral** dan **tiga klaster
masalah** yang saling terkait.

### Ketegangan sentral
SAKIP-Gen **matang pada lapisan rekayasa** (tata kelola, keamanan, abstraksi data, deploy:
⭐⭐⭐⭐–⭐⭐⭐⭐⭐) tetapi **belum matang pada lapisan nilai inti** (kecerdasan evaluasi & kesetiaan
domain SAKIP: ⭐⭐–⭐⭐⭐). Konsekuensinya: sistem **andal menyajikan angka yang belum tentu benar
secara domain** — dan menyajikannya **tanpa peringatan**. Inilah risiko terbesar yang muncul di dua
review sekaligus (KEC & BIS): bukan bug teknis, melainkan **kredibilitas**.

### Tiga klaster masalah yang saling mengikat

```
  KLASTER A — VALIDITAS NILAI (paling kritis, lintas KEC+BIS)
  ├─ Pengukuran abaikan capaian aktual (KEC-1, BIS-3)
  ├─ Komponen Hasil (~40%) hilang (BIS-3)
  ├─ Bobot & sub-aspek tak selaras LKE 88/2021 (KEC-2, BIS-4)
  ├─ Nilai disajikan tanpa disclaimer / salah label (BIS-1, BIS-2)
  └─ Rentan gaming (BIS-5)
        │ (validitas nilai ini menjadi PRASYARAT kebermaknaan semua fitur lain)
        ▼
  KLASTER B — KESIAPAN INTEGRASI (go-live, lintas TEK+DAT)
  ├─ Schema seam belum disesuaikan ke MySQL nyata (TEK-1, DAT-1)  ← seam GANDA: queries.py + promote.py
  ├─ Auth masih in-memory secara default (TEK-2)
  └─ bangun_dosir 4 koneksi terpisah (DAT-2)
        │
        ▼
  KLASTER C — KEMATANGAN AI & OPERASIONAL (penguatan, lintas KEC+TEK+DAT)
  ├─ LLM dangkal, blocking, tanpa cache/retry/biaya (KEC-3, TEK-3, TEK-4)
  ├─ Drafting sempit + deteksi mislabel (KEC-4, KEC-6, BIS-5, BIS-7)
  ├─ Robustness data: SQLAlchemy Core, status sumber-tunggal, Alembic (DAT-3, DAT-5, DAT-4/TEK-7)
  ├─ Observability: /metrics + coverage (TEK-6)
  └─ Skala-keluar + analitik lanjutan: scheduler terpisah/Redis, tren, cascading (TEK-5, KEC-5, BIS-6, BIS-7)
```

**Urutan logis yang dipaksakan oleh dependensi:** *Kejujuran nilai* (murah, mendesak) → *Validitas
nilai* (redesain evaluator) → *Kesiapan integrasi* (go-live) → *Penguatan AI/ops* → *Skala/analitik*.
Catatan penting: **klaster A bagian "kejujuran" (disclaimer/label) harus didahulukan** karena
berbiaya rendah namun menutup risiko kredibilitas seketika, **sebelum** redesain skoring yang lebih
lama.

---

## 2. Matriks keterlacakan (semua temuan → tugas)

Setiap rekomendasi di keempat review dipetakan ke minimal satu tugas. Tidak ada yang terlewat.

| Temuan asal | Prioritas asal | Tugas |
|---|---|---|
| KEC-1 / BIS-3 — capaian aktual masuk skor Pengukuran | 🔴 | **T2.1** |
| BIS-3 — Komponen Hasil (capaian + akuntabilitas keuangan) | 🔴 | **T2.2** |
| KEC-2 / BIS-4 — kalibrasi bobot & sub-aspek (Pemenuhan/Kualitas/Pemanfaatan) ke LKE 88/2021 | 🔴/🟠 | **T2.3** |
| BIS-1 — disclaimer di output bot | 🔴 | **T0.1** |
| BIS-2 — reposisi label "Indeks Kualitas Implementasi SAKIP (proses)" | 🔴 | **T0.2** |
| BIS-5 — pengaman anti-gaming (label vs uraian, bukti flag) | 🟠 | **T2.4** |
| TEK-1 / DAT-1 — sesuaikan schema seam (queries.py **dan** promote.py) + uji integrasi | 🔴 | **T1.1** |
| TEK-2 — `USE_SQL_AUTH` default produksi | 🔴 | **T1.2** |
| DAT-2 — `bangun_dosir` berbagi satu koneksi RO | 🟠 | **T1.3** |
| TEK-3 — lepas LLM dari request webhook (background) | 🟠 | **T3.1** |
| TEK-4 — caching + retry + pelacakan biaya LLM; mutakhirkan model + prompt caching | 🟠 | **T3.2** |
| KEC-3 — perkaya prompt LLM (few-shot + konteks sasaran + satuan) | 🟠 | **T3.3** |
| KEC-6 — deteksi mislabel tipologi via LLM | 🟢 | **T3.4** |
| KEC-4 / BIS-7 — perluas drafting ke gap pengukuran/pelaporan/evaluasi | 🟠/🟢 | **T3.5** |
| DAT-3 — SQLAlchemy Core `Table`/`MetaData` (kurangi typo) | 🟠 | **T4.1** |
| DAT-5 — payload sumber-tunggal status; kolom = projection read-only | 🟢 | **T4.2** |
| TEK-7 / DAT-4 — Alembic untuk migrasi `ai_*` | 🟢 | **T4.3** |
| TEK-6 — `/metrics` (Prometheus) + coverage gate CI | 🟢 | **T4.4** |
| TEK-5 — skala-keluar: scheduler terpisah + Redis limiter + `workers>1` | 🟠 | **T5.1** |
| KEC-5 — analisis tren antar-tahun + benchmark antar-OPD | 🟢 | **T5.2** |
| BIS-6 — manfaatkan `level`: evaluasi cascading/keselarasan | 🟠 | **T5.3** |
| BIS-7 — monitoring target berisiko di push triwulanan | 🟢 | **T5.4** |

---

## 3. Rencana berfase

Prioritas tugas: **P0** (mendesak/quick-win) · **P1** (blokir go-live) · **P2** (inti nilai) ·
**P3** (penguatan) · **P4** (skala). Estimasi: S ≈ ≤0,5 hari, M ≈ 1–2 hari, L ≈ 3–5 hari.

---

### FASE 0 — Kejujuran nilai (quick wins, dahulukan) · P0

Menutup risiko kredibilitas **seketika** dengan perubahan kecil, tanpa menyentuh logika skoring.

**T0.1 — Disclaimer di output pengguna** · S · *tanpa dependensi*
- **Masalah:** BIS-1 — `format_ringkasan`/`format_gap` menyajikan nilai/predikat tanpa peringatan.
- **Aksi:** tambahkan baris peringatan tetap di [bot/format.py](../bot/format.py) (mis. *"Estimasi
  internal SAKIP-Gen — bukan hasil LKE resmi MenPAN-RB."*) dan di footer template
  [web/templates/usulan.html](../web/templates/usulan.html) bila relevan.
- **Selesai bila:** setiap pesan evaluasi/gap memuat disclaimer; uji `tests/` menegaskan substring
  disclaimer ada.

**T0.2 — Reposisi label nilai** · S · *tergantung T0.1*
- **Masalah:** BIS-2 — menyebut "Nilai/Predikat AKIP" menyiratkan hasil resmi.
- **Aksi:** ubah label keluaran menjadi **"Indeks Kualitas Implementasi SAKIP (proses)"** selama
  Komponen Hasil belum ada (T2.2). Sesuaikan judul di `format.py`, `demo_evaluasi.py`, dan doc
  string evaluator. Pertahankan predikat AA–D tetapi beri kualifikasi "(indikatif)".
- **Selesai bila:** tidak ada string "Nilai AKIP/Predikat AKIP" polos di jalur pengguna; istilah
  konsisten lintas bot + demo + docs.

---

### FASE 1 — Kesiapan integrasi / go-live · P1

Prasyarat teknis agar sistem dapat dijalankan dengan MySQL SAKIP nyata.

**T1.1 — Adaptasi & verifikasi schema seam (GANDA)** · L · *tanpa dependensi (paralel dgn Fase 0)*
- **Masalah:** TEK-1 + DAT-1 — SQL mengasumsikan skema referensi; seam tersebar di **dua** file.
- **Aksi:**
  1. Petakan skema SAKIP nyata (`SHOW CREATE TABLE`) → sesuaikan **semua** query di
     [db/queries.py](../db/queries.py) **dan** [db/promote.py](../db/promote.py) (`_SQL_INDIKATOR`,
     `_SQL_UPDATE_IND`) **secara bersamaan**.
  2. Tambah **uji integrasi pemetaan**: fixture skema mendekati produksi → pastikan `bangun_dosir`
     & `terapkan_usulan` menghasilkan kolom yang benar.
  3. Perbarui [db/ddl/schema_referensi.sql](../db/ddl/schema_referensi.sql) agar mencerminkan
     pemetaan final.
- **Risiko:** salah satu file terlewat = bug senyap → wajib uji integrasi yang menyentuh kedua jalur.
- **Selesai bila:** `pytest` hijau dengan fixture skema realistis; `python -m deploy.preflight`
  menyambung ke tiga engine pada MySQL nyata.

**T1.2 — `USE_SQL_AUTH` sebagai default produksi** · M · *tergantung T1.1 (engine staging siap)*
- **Masalah:** TEK-2 — repo auth in-memory hilang saat restart, tak konsisten multi-worker.
- **Aksi:** terapkan DDL [db/ddl/auth.sql](../db/ddl/auth.sql); jadikan `use_sql_auth=true` default
  untuk `env=production` (atau peringatkan di `audit_keamanan` bila `production` + in-memory);
  seed kode pendaftaran via `SqlAuthRepository.tambah_kode`.
- **Selesai bila:** pendaftaran & pengguna bertahan lintas restart; uji menutup jalur SQL repo.

**T1.3 — `bangun_dosir` berbagi satu koneksi RO** · S · *tergantung T1.1*
- **Masalah:** DAT-2 — 4 koneksi terpisah → tanpa snapshot konsisten + 4 round-trip.
- **Aksi:** refactor `ambil_*` agar menerima `conn` opsional; `bangun_dosir` membuka satu
  `connect()` dan membaginya ke keempat sub-fungsi.
- **Selesai bila:** satu koneksi per evaluasi; uji `tests/test_fase1.py` tetap hijau.

---

### FASE 2 — Validitas nilai & kesetiaan SAKIP (inti) · P2

Redesain evaluator agar nilainya bermakna secara domain. **Klaster paling konsekuensial.**

**T2.1 — Capaian aktual ke skor Pengukuran** · M · *tergantung T1.1*
- **Masalah:** KEC-1 + BIS-3 — `_skor_pengukuran` hanya menilai kelengkapan data.
- **Aksi:** integrasikan `persen_capaian` ke skor (mis. gabungkan kelengkapan *dan* tingkat
  capaian ber-cap pada 100%); tambah `GapTemuan` untuk indikator dengan capaian rendah. Perbarui
  [agent/evaluator.py](../agent/evaluator.py) + [docs/DATA_MODEL.md](DATA_MODEL.md).
- **Selesai bila:** OPD dengan data lengkap tapi realisasi rendah **tidak** lagi mendapat skor
  penuh; uji baru menegaskan sensitivitas terhadap capaian.

**T2.2 — Tambahkan Komponen Hasil** · L · *tergantung T2.1*
- **Masalah:** BIS-3 — komponen hasil (~40% pada 88/2021) hilang total.
- **Aksi:** rancang komponen "Hasil" (capaian kinerja organisasi + akuntabilitas keuangan);
  perluas model `DosirKinerja` ([agent/dosir.py](../agent/dosir.py)) dengan data keuangan/capaian
  agregat; tambah query sumber terkait (seam — koordinasikan dgn T1.1). Setelah ini, **cabut
  kualifikasi label** dari T0.2 (boleh kembali menyebut estimasi nilai AKIP, tetap dengan
  disclaimer).
- **Selesai bila:** nilai total mencakup dimensi hasil; struktur mendekati pengungkit+hasil.

**T2.3 — Kalibrasi bobot & tiga sub-aspek ke LKE 88/2021** · L · *tergantung T2.2*
- **Masalah:** KEC-2 + BIS-4 — bobot 30/30/15/25 & penilaian "Pemenuhan saja".
- **Aksi:** sejajarkan bobot dengan instrumen LKE **terbaru** (verifikasi pedoman teknis berlaku);
  perluas tiap komponen pengungkit ke **Pemenuhan / Kualitas / Pemanfaatan**; jadikan bobot
  konfigurabel (hindari hard-code) agar mudah dikalibrasi ulang.
- **Selesai bila:** bobot & sub-aspek terdokumentasi + dapat dikonfigurasi; uji regresi skor.

**T2.4 — Pengaman anti-gaming** · M · *tergantung T2.1*
- **Masalah:** BIS-5 — skor naik via relabel/centang tanpa perbaikan nyata.
- **Aksi:** heuristik (opsional LLM) menandai indikator berlabel `outcome` yang `uraian`-nya masih
  berbunyi output; tandai flag `pelaporan_meta` tanpa bukti pendukung sebagai "perlu verifikasi".
- **Selesai bila:** evaluasi memunculkan peringatan integritas; uji untuk kasus relabel.

---

### FASE 3 — Kematangan AI & cakupan drafting · P3

**T3.1 — Lepas LLM dari request webhook** · M · *tergantung tidak ada (boleh paralel Fase 2)*
- **Masalah:** TEK-3 — `dp.feed_update` blocking; `/usul`+LLM bisa memicu timeout Telegram.
- **Aksi:** jadikan `/usul` dua langkah (balas cepat "menyusun…", proses LLM di background task,
  lalu edit/kirim hasil) atau pakai `asyncio` task terlepas dari handler.
- **Selesai bila:** handler kembali < ~1–2 dtk; hasil LLM menyusul tanpa retry Telegram.

**T3.2 — Caching + retry + biaya + model + prompt caching** · M · *tergantung T3.1*
- **Masalah:** TEK-4 — tiap panggilan berbayar, tanpa cache/retry; model perlu dimutakhirkan.
- **Aksi:** memoisasi hasil identik (kunci = hash uraian+tipologi); retry/backoff + circuit
  breaker; catat biaya/token ke event log; mutakhirkan model & terapkan prompt caching
  (gunakan skill `claude-api`) di [agent/llm.py](../agent/llm.py).
- **Selesai bila:** panggilan identik tak berulang; kegagalan API tertangani anggun; biaya tercatat.

**T3.3 — Perkaya prompt LLM** · S · *tergantung T3.2*
- **Masalah:** KEC-3 — prompt single-shot tanpa konteks.
- **Aksi:** sertakan few-shot contoh output→outcome SAKIP, **uraian sasaran strategis** induk, dan
  `satuan` pada prompt ([agent/llm.py](../agent/llm.py), [agent/improver.py](../agent/improver.py)).
- **Selesai bila:** rumusan outcome lebih spesifik & selaras sasaran (uji manual + sampel).

**T3.4 — Deteksi mislabel tipologi** · M · *tergantung T3.2, T2.4*
- **Masalah:** KEC-6 — kurangi GIGO dari label tipologi salah di MySQL.
- **Aksi:** verifikasi semantik (LLM) atas tipologi vs `uraian`; suarakan sebagai temuan integritas
  (bukan mengubah data). Bersinergi dengan T2.4.
- **Selesai bila:** indikator salah-label tertandai pada evaluasi.

**T3.5 — Perluas cakupan drafting** · L · *tergantung T2.1, T2.2*
- **Masalah:** KEC-4 + BIS-7 — hanya tipe `perbaikan_indikator`.
- **Aksi:** tambah tipe usulan untuk gap **pengukuran** (lengkapi capaian), **pelaporan** (kerangka
  LKjIP/analisis), **evaluasi internal**; sesuaikan UI form & whitelist promosi bila perlu.
- **Selesai bila:** `/usul` menghasilkan usulan untuk lebih dari satu jenis gap; uji per tipe.

---

### FASE 4 — Robustness data & observability · P3

**T4.1 — SQLAlchemy Core `Table`/`MetaData`** · M · *tergantung T1.1*
- **Masalah:** DAT-3 — SQL string mentah rawan typo kolom.
- **Aksi:** definisikan tabel sumber & `ai_*` sekali via `MetaData`; bangun query dari objek kolom
  (tetap tanpa ORM penuh) di `db/queries.py`, `db/staging.py`, `db/promote.py`.
- **Selesai bila:** referensi kolom terpusat; typo tertangkap lebih awal; uji tetap hijau.

**T4.2 — Payload sumber-tunggal status** · S · *tergantung T4.1*
- **Masalah:** DAT-5 — duplikasi `status` kolom↔payload berisiko drift.
- **Aksi:** tegaskan kolom denormalisasi sebagai **projection read-only**; pada baca, status dari
  kolom otoritatif (sudah), dan dokumentasikan invariannya; tambah uji yang menjaga sinkronisasi.
- **Selesai bila:** invarian terdokumentasi + teruji; tak ada jalur tulis yang melewatkan sinkron.

**T4.3 — Alembic untuk migrasi `ai_*`** · M · *tergantung T4.1*
- **Masalah:** TEK-7 + DAT-4 — DDL manual → drift antar lingkungan.
- **Aksi:** inisialisasi Alembic untuk tabel milik agen (`ai_usulan`, `ai_audit`, `ai_event`,
  auth); pertahankan tabel sumber **di luar** kendali migrasi (milik aplikasi SAKIP).
- **Selesai bila:** `alembic upgrade head` membangun skema `ai_*`; runbook deploy diperbarui.

**T4.4 — `/metrics` + coverage gate** · M · *tanpa dependensi kuat*
- **Masalah:** TEK-6 — observability log-sentris, tanpa metrik/coverage.
- **Aksi:** tambah endpoint Prometheus (jumlah evaluasi, usulan, error, latensi, hit/miss limiter);
  tambah `pytest --cov` + ambang minimum di CI (`ci.yml`).
- **Selesai bila:** `/metrics` aktif; CI gagal bila coverage < ambang.

---

### FASE 5 — Skala & analitik lanjutan · P4

**T5.1 — Jalur skala-keluar** · L · *tergantung T4.4 (metrik untuk memantau)*
- **Masalah:** TEK-5 — plafon 1 worker (scheduler in-process + limiter per-proses).
- **Aksi:** pisahkan scheduler ke service tersendiri (`ENABLE_SCHEDULER=false` pada web); pindahkan
  limiter/throttle ke Redis di belakang antarmuka `cek()` yang ada ([web/ratelimit.py](../web/ratelimit.py),
  [bot/throttle.py](../bot/throttle.py)); baru naikkan `workers` di
  [deploy/gunicorn.conf.py](../deploy/gunicorn.conf.py).
- **Selesai bila:** multi-worker tanpa push ganda & dengan limiter konsisten.

**T5.2 — Tren antar-tahun & benchmark antar-OPD** · L · *tergantung T2.3*
- **Masalah:** KEC-5 — analisis statis satu tahun/OPD.
- **Aksi:** tambah perbandingan nilai antar-tahun & antar-OPD pada evaluasi/laporan; perkaya
  format pesan & (opsional) Mini App.
- **Selesai bila:** evaluasi menampilkan delta tahun & posisi relatif; uji agregasi.

**T5.3 — Evaluasi cascading/keselarasan (`level`)** · L · *tergantung T2.3*
- **Masalah:** BIS-6 — field `level` diabaikan; cascading tak dinilai.
- **Aksi:** modelkan keselarasan RPJMD→Renstra→Renja→PK dan antar-eselon (dinas/bidang/seksi);
  manfaatkan `UsulanPerbaikan.level`; tambah komponen/gap keselarasan.
- **Selesai bila:** evaluasi menyertakan dimensi cascading; uji kasus tak-selaras.

**T5.4 — Monitoring target berisiko (push triwulanan)** · M · *tergantung T2.1, T5.1*
- **Masalah:** BIS-7 — push triwulanan hanya ringkasan statis.
- **Aksi:** di [bot/scheduler.py](../bot/scheduler.py), tandai indikator dengan capaian di bawah
  ambang sebagai "berisiko" dan dorong peringatan dini.
- **Selesai bila:** push memuat daftar indikator berisiko; uji ambang.

---

## 4. Ringkasan urutan & ketergantungan

```
Fase 0 (P0)  T0.1 → T0.2                         [quick wins, segera]
Fase 1 (P1)  T1.1 ┬→ T1.2                         [go-live]   (T1.1 paralel dgn Fase 0)
                  └→ T1.3
Fase 2 (P2)  T2.1 → T2.2 → T2.3                   [inti nilai]
                  └→ T2.4
Fase 3 (P3)  T3.1 → T3.2 → T3.3                   [AI]        (T3.1 paralel dgn Fase 2)
                          → T3.4
             T2.1,T2.2 → T3.5                     [drafting]
Fase 4 (P3)  T1.1 → T4.1 ┬→ T4.2
                         └→ T4.3 ;  T4.4 (mandiri)
Fase 5 (P4)  T4.4 → T5.1 ;  T2.3 → T5.2, T5.3 ;  T2.1+T5.1 → T5.4
```

**Jalur kritis menuju "produk SAKIP kredibel & siap pakai":**
`T0.1/T0.2` (kejujuran) → `T1.1` (integrasi) → `T2.1 → T2.2 → T2.3` (validitas nilai). Setelah jalur
ini, sistem layak dipakai untuk keputusan indikatif; sisanya adalah penguatan.

| Fase | Tugas | Total estimasi kasar |
|---|---|---|
| 0 — Kejujuran | T0.1, T0.2 | ~1 hari |
| 1 — Integrasi | T1.1, T1.2, T1.3 | ~1 minggu |
| 2 — Validitas nilai | T2.1, T2.2, T2.3, T2.4 | ~2 minggu |
| 3 — AI & drafting | T3.1–T3.5 | ~2 minggu |
| 4 — Robustness/ops | T4.1–T4.4 | ~1,5 minggu |
| 5 — Skala/analitik | T5.1–T5.4 | ~3 minggu |

---

## 5. Prinsip pelaksanaan (lintas-tugas)

1. **Pertahankan empat pilar tata kelola** (sumber tunggal MySQL, akses agen read-only, agen
   evaluator+drafter, human-in-the-loop+audit) — tidak ada tugas yang boleh melanggarnya.
2. **Setiap tugas menyertakan/memperbarui uji** `tests/test_faseN.py` & dokumen `docs/` terkait
   (konvensi repo); jalankan `python -m pytest -q` + `ruff` + `mypy` sebelum selesai.
3. **Bobot & ambang skoring harus konfigurabel** (T2.3) agar kalibrasi LKE berikutnya tak menyentuh
   kode.
4. **Verifikasi regulatif:** angka/struktur LKE (bobot, sub-aspek, ambang) dikonfirmasi ke pedoman
   teknis SAKIP **terbaru** sebelum dikunci (lihat catatan di [REVIEW_SAKIP_BISNIS.md](REVIEW_SAKIP_BISNIS.md)).
5. **Jangan menaikkan `workers`** sampai T5.1 selesai (scheduler + limiter belum aman multi-proses).
6. **Schema seam selalu diubah berpasangan** (`queries.py` + `promote.py`) dengan uji integrasi
   yang menyentuh kedua jalur.

---

## 6. Kesimpulan

Empat review menunjuk pada **satu prioritas tunggal yang menyatukan semuanya: jadikan nilai yang
disajikan benar dan jujur sebelum menambah kecanggihan.** Karena itu rencana ini menempatkan
**kejujuran (Fase 0)** dan **validitas nilai (Fase 2)** di jalur kritis, dengan **kesiapan integrasi
(Fase 1)** sebagai prasyarat operasional. Kematangan AI, robustness, dan skala (Fase 3–5) penting
tetapi **sekunder**: tanpa nilai yang sahih, penguatan apa pun hanya mempercepat penyajian angka
yang belum tentu benar. Mengeksekusi Fase 0–2 saja sudah mengubah SAKIP-Gen dari *demonstrator
arsitektur yang rapi* menjadi *alat bantu SAKIP yang kredibel*.
