# SAKIP-Gen — Antarmuka (v1.0)

## 1. Perintah bot Telegram
**Perintah publik (tanpa pendaftaran):** `/start`, `/help`, `/ping`, `/daftar`.
Selain itu **memerlukan akun terdaftar** (disuntik oleh `AuthMiddleware`); akses OPD dibatasi
`boleh_opd()`, dan promosi oleh `boleh_promosi()` (peran `kepala_dinas`/`admin`).

Setiap perintah `/slash` dan setiap kalimat bahasa alami menghasilkan objek **`Permintaan`** yang
sama, lalu dieksekusi oleh satu dispatcher (`_jalankan`).

| Perintah | Akses | Fungsi |
|---|---|---|
| `/start` | publik | Perkenalan + arahan mendaftar |
| `/help` | publik | Daftar perintah singkat¹ |
| `/ping` | publik | Cek bot (`pong`) |
| `/daftar <kode>` | publik | Mendaftar dengan kode sekali-pakai (menu menyesuaikan peran) |
| `/status` | terdaftar | Akun, peran, OPD, & hak promosi |
| `/opd` | terdaftar | Daftar/cari OPD (resolusi id/kode/nama) |
| `/evaluasi` \| `/nilai <opd> [tahun]` | terdaftar + `boleh_opd` | Ringkasan evaluasi LKE (skor, predikat, gap) |
| `/gap <opd> [tahun]` | terdaftar + `boleh_opd` | Daftar gap berprioritas |
| `/rencana <opd> [tahun] [dok]` | terdaftar + `boleh_opd` | Perencanaan: sasaran, IKU, keselarasan/cascading |
| `/capaian <opd> [tahun]` | terdaftar + `boleh_opd` | Target vs realisasi (per periode TW/semester) |
| `/laporan <opd> [tahun]` | terdaftar + `boleh_opd` | Draft bahan LKjIP (analisis capaian via LLM) |
| `/temuan <opd> [tahun]` | terdaftar + `boleh_opd` | Temuan internal + rekomendasi + tindak lanjut |
| `/dokumen <opd> [tahun] [jenis]` | terdaftar + `boleh_opd` | Telusur dokumen SAKIP + versi & bukti |
| `/tren <opd> [tahun]` | terdaftar + `boleh_opd` | Tren nilai antar-tahun |
| `/benchmark [tahun]` | terdaftar | Peringkat antar-OPD (lingkup pengguna/semua untuk admin) |
| `/usul <opd> [tahun]` | terdaftar + `boleh_opd` | Buat draft usulan + tombol form/Setujui/Tolak |
| `/usulan <opd>` | terdaftar + `boleh_opd` | Daftar usulan per OPD (status) |
| `/terapkan <usulan_id>` | terdaftar + `boleh_promosi` | Konfirmasi → terapkan usulan ke sumber |

¹ Catatan v1.0: teks `/help` bawaan menampilkan **sebagian** perintah inti; daftar lengkap tersedia
lewat **menu perintah Telegram per peran** (§5) dan respons klarifikasi bahasa alami.

**Parameter:** `tahun` opsional (default tahun berjalan). `opd` numerik pada `/slash`. Argumen
opsional `/rencana` & `/dokumen`: token angka 4-digit → tahun; kata jenis dokumen → slot `dokumen`
(`rpjmd·renstra·renja·rkpd·pk·pohon·lkjip·lhe`). Untuk `/capaian`, periode diambil dari bahasa
alami ("triwulan 2", "semester 1") atau default tahunan.

**Callback (tombol inline):** `setuju:<id>`, `tolak:<id>` (memutuskan usulan); `terapkan_ok:<id>`,
`terapkan_batal:<id>` (konfirmasi penerapan). Semua callback melewati RBAC yang sama.

## 2. Bahasa alami (NL → Permintaan)
Pengguna dapat menulis kalimat biasa; `nl_handler` menangani teks non-`/slash`. Pipeline anti-halu
(`agent/nlu.py`):
1. **Heuristik** `parse()` — offline, selalu tersedia.
2. **LLM terstruktur** `parse_llm()` — *fallback* bila heuristik gagal & LLM tersedia (enum tertutup).
3. **Grounding** `cocokkan_opd()` — OPD wajib resolusi ke entitas nyata.
4. **Putusan**: eksekusi, slot-filling, atau **klarifikasi sopan**.

Contoh: *"nilai dinas pendidikan triwulan 2 2026"*, *"capaian opd 1"*, *"apa kelemahan DIKBUD"*,
*"lihat pohon kinerja opd 1"*, *"draft analisis LKjIP opd 1"*, *"bandingkan OPD 2026"*.

Aturan keras:
- Niat tak terdeteksi → "Maaf, saya belum menangkap maksud Anda…" + saran verba (bukan error).
- OPD kurang/ambigu → "OPD mana yang Anda maksud?" + contoh id/kode (bukan 404).
- Tak berwenang → pesan ramah (bukan 403). Data gagal → "coba lagi sebentar" (bukan stack trace).
- `/terapkan` **tidak** dapat dipicu lewat bahasa alami (wajib `/slash` + konfirmasi).

Observability: `sakipgen_nlu_total{hasil=heuristik|llm|klarifikasi|tak_paham}`.

## 3. Endpoint HTTP
Base URL produksi = `PUBLIC_BASE_URL` (mis. `https://ai.contoh.id`).

| Metode & path | Auth | Keterangan |
|---|---|---|
| `GET /healthz` | — | `{"status":"ok","service":"sakip-gen","version":"1.0.0"}` |
| `GET /readyz` | — | Kesiapan: cek koneksi engine RO/staging/promotor (503 bila gagal) |
| `GET /metrics` | — | Metrik Prometheus (text/plain; version=0.0.4) |
| `POST /webhook/<WEBHOOK_SECRET>` | Header secret | Endpoint webhook Telegram |
| `GET /usulan?t=<token>` | Token opaque | Render form Mini App |
| `POST /api/usulan/simpan` | initData + token (rate-limited) | Simpan/Setujui usulan dari form |
| `GET /docs`, `GET /redoc` | — | Dokumentasi OpenAPI (FastAPI) |

### 3.1 `GET /readyz`
Memanggil `web.health.readiness` untuk ketiga engine. Respons `{"ready": bool, "checks": {...}}`
dengan status **200** bila semua OK, **503** bila ada engine yang gagal terhubung.

### 3.2 `GET /metrics`
Eksposisi counter Prometheus: `sakipgen_evaluasi_total`, `sakipgen_usulan_total`,
`sakipgen_penerapan_total{hasil}`, `sakipgen_llm_total{hasil}`, `sakipgen_nlu_total{hasil}`,
`sakipgen_error_total`.

### 3.3 `POST /webhook/<WEBHOOK_SECRET>`
Telegram mengirim header `X-Telegram-Bot-Api-Secret-Token`. Server membandingkannya dengan
`WEBHOOK_SECRET` secara **konstan-waktu** (`hmac.compare_digest`); jika tidak cocok → **403**.
Body = objek Update Telegram → diteruskan ke dispatcher → `{"ok":true}`.

### 3.4 `GET /usulan?t=<token>`
`t` = token bertanda tangan & berbatas waktu (default 1 jam). Valid → render `usulan.html`.
Token tidak sah/kedaluwarsa → **403**; usulan tidak ada → **404**.

### 3.5 `POST /api/usulan/simpan`
Dilindungi rate limit (`API_RATE_PER_MENIT`, default 30/menit per klien; kelebihan → **429** +
`Retry-After`). Body JSON:
```json
{
  "initData": "<Telegram.WebApp.initData>",
  "token": "<token dari URL form>",
  "data": {
    "perubahan": [{"field": "uraian", "lama": "...", "usulan": "..."}],
    "alasan": "catatan peninjau",
    "hash_data_lama": "<sha256 saat form dibuka>"
  }
}
```
Urutan pemeriksaan (gagal → kode di kurung):
1. `validasi_init_data` (HMAC bot token) → telegram_id (**403**)
2. `baca_token` sah (**403**)
3. token milik pengguna ini: `token.t == telegram_id` (**403**)
4. usulan ada (**404**)
5. RBAC: `user.boleh_opd(usulan.opd_id)` (**403**)
6. data belum basi: `data.hash_data_lama == usulan.hash_data_lama` (**409**)

Sukses → `{"ok": true, "usulan_id": <id>, "status": "disetujui"}` dan dicatat ke `ai_event`.

## 4. Alur Mini App
1. `/usul` membuat draft (`ai_usulan`, status `draft`) dan token, lalu mengirim tombol **web_app**
   ke `MINIAPP_BASE_URL` atau `PUBLIC_BASE_URL/usulan` dengan `?t=<token>`. Penghalusan rumusan LLM
   berjalan di latar dan menyusul lewat *edit* pesan.
2. Webview membuka `GET /usulan?t=...` → form menampilkan perubahan (lama→usulan) yang dapat diedit.
3. Tombol utama Telegram → konfirmasi → `POST /api/usulan/simpan` (membawa `initData`, `token`, `data`).
4. Server memvalidasi (lihat 3.5) lalu set status `disetujui`. Webview ditutup.

> Webview **tidak pernah** menyentuh MySQL; ia hanya memanggil API di atas (pola "Gerbang").

## 5. Menu perintah per peran (`bot/menu.py`)
`setMyCommands` dipasang **per scope**:
- **Default global** (`MENU_UMUM`): `/nilai`, `/capaian`, `/opd`, `/status`, `/help`.
- **Per-chat sesuai peran** (`MENU_PERAN`): dipasang saat startup untuk tiap admin allowlist, dan
  setelah `/daftar` berhasil untuk pengguna sesuai perannya.

| Peran (enum) | Persona | Menu |
|---|---|---|
| `operator` | Kasubbag Perencanaan / staf | rencana, capaian, nilai, gap, usul, laporan, temuan, dokumen |
| `kepala_dinas` | Kepala Dinas | nilai, capaian, gap, tren, benchmark, laporan, usulan, terapkan |
| `admin` | Evaluator Kabupaten / Admin | nilai, benchmark, temuan, rencana, capaian, dokumen, usulan, terapkan |

Telegram tak punya scope "peran"; menu peran dipasang pada chat privat pengguna (scope chat).

## 6. Push terjadwal
`bot/scheduler.py` menjadwalkan `kirim_ringkasan_terjadwal` tiap **1 Jan/Apr/Jul/Okt pukul 07:00**:
untuk setiap pengguna terdaftar dan tiap OPD-nya, evaluasi lalu kirim ringkasan. Aktif bila
`ENABLE_SCHEDULER=true` (di produksi 1 worker; dapat dipisah ke `scheduler_service.py`).
