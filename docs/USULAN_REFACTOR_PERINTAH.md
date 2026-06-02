# Usulan Refactor Perintah Terpadu SAKIP-Gen

> Menyatukan SELURUH perintah ke dalam **satu tata bahasa**: setiap permintaan =
> **AKSI × OBJEK × LINGKUP × WAKTU**. Slot yang sama (periode, tahapan SAKIP, OPD,
> jenis dokumen, level, fokus) dipakai bersama oleh `/slash` **dan** bahasa alami,
> dieksekusi oleh **satu dispatcher**. Di depannya berdiri **translator bahasa alami
> yang cerdas, anti‑gagal, dan anti‑halu** (§3A): LLM hanya menerjemahkan niat (bukan
> sumber jawaban), dan bila perintah tak dikenali bot menjawab dengan **klarifikasi
> sopan** — tidak pernah menampilkan pesan error teknis. Tanggal: 2026-06-02.
> Status: **TERIMPLEMENTASI** (R1–R5 selesai; lihat §10). 101 test lulus, ruff bersih.

---

## 1. Prinsip
1. **Perintah = kata kerja (aksi)**, dokumen/tahapan/periode = **parameter** — bukan perintah sendiri (hindari ledakan perintah).
2. **Satu tata bahasa** untuk slash & bahasa alami → keduanya menghasilkan objek `Permintaan` yang sama → **satu dispatcher**.
3. **Baca + nilai + draft + usulkan**, bukan menyusun dokumen resmi (RPJMD/Renstra/PK tetap di eSAKIP/Bappeda). Perubahan data hanya via promosi teraudit.
4. **Sadar peran** (Kasubbag Perencanaan · Kadis · Evaluator Kabupaten) — menu & lingkup default berbeda.
5. **Kompatibel mundur**: sintaks lama (`/evaluasi 1 2026`) tetap jalan sebagai bentuk ringkas.

---

## 2. Tata bahasa terpadu — slot `Permintaan`

| Slot | Nilai | Default | Dipakai untuk |
|---|---|---|---|
| `aksi` | rencana·capaian·nilai·laporan·temuan·banding·perbaiki·dokumen·terapkan·akun·opd·bantuan | — | verba (lihat §4) |
| `opd` | id / kode / nama / `saya` / `semua` | `saya` (OPD pengguna) | lingkup organisasi |
| `tahun` | 4 digit | tahun berjalan | waktu |
| `periode` | tahunan · tw1..tw4 · smt1 · smt2 | tahunan | pengukuran berkala |
| `tahapan` | perencanaan · pengukuran · pelaporan · evaluasi · tindak_lanjut | (dari aksi) | menyaring fase SAKIP |
| `dokumen` | rpjmd · renstra · renja · rkpd · pk · pohon · lkjip · lhe | (dari aksi) | objek dokumen |
| `level` | pemda · opd · unit · individu | opd | cascading / PK berjenjang |
| `fokus` | teks bebas (mis. "indikator non-outcome", "efisiensi anggaran") | — | nuansa untuk LLM |

---

## 3. Dua cara input → satu `Permintaan`

**(a) Slash — ringkas (posisional) atau bernama (flag):**
```
/nilai 1 2026                         # posisional: opd=1, tahun=2026
/nilai opd=DIKBUD thn=2026 tw=2        # bernama
/rencana 1 dok=pk level=unit          # PK eselon, OPD 1
/laporan 1 2026 dok=lkjip fokus=efisiensi
/capaian semua thn=2026 tw=3          # evaluator: semua OPD, triwulan 3
```
Aturan: token pertama tanpa `=` → `opd`; token kedua angka → `tahun`. Flag: `opd= thn=/tahun= tw=/smt=/periode= dok= level= tahap= fokus=`.

**(b) Bahasa alami — slot diekstrak heuristik + fallback LLM (Haiku):**
```
"nilai AKIP dinas pendidikan triwulan 2 2026"
"lihat pohon kinerja & PK eselon III opd 1"
"buatkan draft analisis efisiensi untuk LKjIP opd 1 2026"
"bandingkan semua OPD tahun 2026"
```

Keduanya → `Permintaan(aksi=…, opd=…, tahun=…, periode=…, dokumen=…, level=…, fokus=…)` → **`dispatch(permintaan, user)`**.

---

## 3A. Translator Bahasa Alami — Cerdas · Anti‑Gagal · Anti‑Halu

> Prinsip inti **anti‑halu**: **LLM hanya MENERJEMAHKAN niat & MENGEKSTRAK slot dari kalimat
> pengguna — tidak pernah menjawab fakta, menilai, atau mengarang data.** Seluruh angka,
> skor, dan daftar SELALU berasal dari evaluator + basis data; LLM bukan sumber jawaban.
> Dengan begitu LLM tak bisa "berhalusinasi" nilai/OPD/temuan.

### Pipeline 5 lapis (turun bertingkat, tiap lapis aman)
```
Teks pengguna
  └─0. Normalisasi (trim, lower, buang tanda baca berlebih, batasi panjang)
  └─1. HEURISTIK deterministik  →  kandidat Permintaan + skor keyakinan
        • cepat, gratis, OFFLINE (selalu tersedia walau LLM mati)
  └─2. Bila skor rendah/ambigu → FALLBACK LLM TERSTRUKTUR (Haiku)
        • keluaran JSON ber-skema dengan enum tertutup (bukan prosa)
        • retry + timeout + circuit breaker (sudah ada di agent/llm)
  └─3. GROUNDING & VALIDASI tiap slot ke entitas/nilai NYATA
  └─4. Putuskan:  EKSEKUSI  |  ISI-SLOT (slot-filling)  |  KLARIFIKASI
```

### Guardrail anti‑halu (validasi keras sebelum eksekusi)
| Slot | Aturan grounding | Bila gagal |
|---|---|---|
| `aksi` | wajib ∈ enum tertutup (13 verba); apa pun di luar → ditolak | klarifikasi |
| `opd` | wajib **resolve ke OPD nyata** (`cocokkan_opd` vs `daftar_opd`) | tanya OPD (jangan tebak) |
| `tahun` | 4 digit & rentang wajar (mis. 2015–2100) | pakai tahun berjalan / tanya |
| `periode` | ∈ {tahunan, tw1..tw4, smt1, smt2} | default tahunan |
| `dokumen`/`level` | ∈ enum | abaikan nilai tak sah |
| (semua) | nilai yang **tak disebut** di kalimat = `null` — LLM **dilarang mengisi karangan**; di-cross-check ke teks asli | abaikan |

Tambahan kunci: **LLM tidak pernah mengeksekusi**. Ia hanya mengusulkan `Permintaan`; kode yang memvalidasi & menjalankan. Untuk skema terstruktur dipakai `output_config.format` (json_schema, `aksi` ber-`enum`) pada Haiku 4.5 → keluaran dijamin salah‑satu nilai sah, bukan teks bebas.

### Anti‑gagal (fail‑safe berlapis)
- **Heuristik selalu jalan** tanpa jaringan/LLM → frasa umum tetap dipahami saat LLM mati.
- **LLM**: retry+timeout+circuit‑breaker; bila gagal → turun ke heuristik; bila itu pun nihil → klarifikasi sopan.
- **Semua pengecualian ditelan** di lapisan dispatcher → pengguna **TIDAK PERNAH** melihat "Error/Traceback/500/KeyError". Detail teknis hanya ke log + counter; ke pengguna hanya pesan ramah (opsional kode rujukan singkat untuk dukungan).

### Klarifikasi sopan — BUKAN pesan error
| Situasi | Respons (ramah, + tombol bila perlu) |
|---|---|
| Niat tak terdeteksi | "Maaf, saya belum menangkap maksud Anda. Mungkin salah satu ini?" + tombol: Nilai · Capaian · Gap · Usul · Laporan · Banding |
| Niat jelas, OPD kurang/ambigu | "OPD mana yang Anda maksud?" + tombol daftar OPD (atau minta sebut id/kode/nama) |
| Ambigu antara 2 niat | "Maksud Anda **menilai** atau **melihat capaian**?" + 2 tombol |
| `/capaian` tanpa periode | "Untuk periode apa?" + tombol TW1–TW4 / Tahunan |
| OPD tak ditemukan | "OPD ‘X’ belum saya temukan. Ini daftar OPD yang tersedia: …" (bukan 404) |
| Tak berwenang | "Sepertinya Anda belum punya akses ke OPD itu. Hubungi admin bila perlu." (bukan 403) |
| Data sedang gagal diambil | "Maaf, data sedang tidak bisa diambil. Coba lagi sebentar ya." (bukan stack trace) |
| `terapkan` via NL | "Penerapan ke data resmi perlu langkah eksplisit demi keamanan. Gunakan /terapkan lalu konfirmasi." |

Slot‑filling & disambiguasi memakai **inline button** yang membawa `Permintaan` parsial terkode di `callback_data` (mis. `niat:nilai:opd=1`) → **stateless**, pengguna tinggal menekan untuk melengkapi (tak perlu mengetik ulang).

### Ambang keyakinan
- Skor heuristik = fungsi jumlah & spesifisitas kata kunci yang cocok; LLM menyertakan flag keyakinan.
- **Di bawah ambang → klarifikasi, bukan eksekusi** (mencegah menjalankan aksi yang salah). Lebih baik bertanya daripada salah/berhalusinasi.

### Observability
Counter `sakipgen_nlu_total{hasil=heuristik|llm|klarifikasi|tak_paham}` + log ringkas tiap terjemahan (tanpa data sensitif) untuk memantau akurasi & kebutuhan penambahan kata kunci.

### Contoh
- *"nilai dinas pendidikan triwulan 2"* → heuristik: aksi=nilai? (NL "triwulan 2"→periode=tw2), opd_ref="dinas pendidikan" → grounding cocokkan ke OPD nyata → eksekusi `/nilai opd=1 tw=2`.
- *"gimana ya opd itu"* → niat & OPD tak jelas → "Maaf, belum jelas. Mau **nilai**, **capaian**, atau **gap**? OPD mana?" + tombol.
- *"hapus semua data"* → tak ada aksi sah → klarifikasi sopan (tak melakukan apa pun).

---

## 4. Daftar verba (13) + slot yang dipakai

| Verba | Tahapan | Slot relevan | Output | Peran utama | Status |
|---|---|---|---|---|---|
| `/rencana` | Perencanaan | opd, tahun, **dokumen** (rpjmd/renstra/renja/pk/pohon), **level** | Dosir perencanaan: sasaran, IKU, indikator, keselarasan/cascading; sorot non-outcome | Kasubbag, Evaluator | **baru** |
| `/capaian` | Pengukuran | opd, tahun, **periode** | Target vs realisasi, %; indikator berisiko (capaian rendah) | Kasubbag, Kadis | **baru** |
| `/nilai` | Evaluasi (LKE) | opd, tahun | Skor 5 komponen, predikat, gap teratas (estimasi indikatif) | Semua | ada (=/evaluasi+/gap) |
| `/laporan` | Pelaporan | opd, tahun, **dokumen** (lkjip/lhe), **fokus** | Draft narasi LKjIP/LHE (analisis capaian & efisiensi) via LLM | Kasubbag, Evaluator | **baru** |
| `/temuan` | Evaluasi internal + TL | opd, tahun, status | Temuan + rekomendasi APIP + status tindak lanjut | Evaluator, Kasubbag | **baru** |
| `/banding` | Lintas | opd\|`semua`, tahun | Tren antar-tahun (1 OPD) + benchmark antar-OPD + rata-rata kabupaten | Kadis, Evaluator | ada (=/tren+/benchmark) |
| `/perbaiki` | Aksi (perencanaan) | opd, tahun | Usulan indikator output→outcome (LLM) → antrean persetujuan | Kasubbag | ada (=/usul+/usulan) |
| `/terapkan` | Tata kelola | id usulan | Promosi ke data sumber (konfirmasi + audit) | Kadis/Admin | ada |
| `/dokumen` | Lintas | opd, tahun, **dokumen** | Telusur berkas + versi + bukti (dokumen, dokumen_versi, dokumen_bukti) | Semua | **baru (opsional)** |
| `/opd` | — | (cari) | Daftar/cari OPD (resolusi id/kode/nama) | Semua | baru |
| `/akun` | — | — | Peran, OPD, hak | Semua | ada (=/status) |
| `/bantuan` | — | — | Bantuan kontekstual (di-LLM-kan) | Semua | ada (=/help) |
| `/mulai` | — | — | Onboarding | Semua | ada (=/start) |

---

## 5. Matriks Tahapan SAKIP × Verba × Dokumen × Peran

| Tahapan | Dokumen terkait | Verba | Kasubbag | Kadis | Evaluator |
|---|---|---|---|---|---|
| Perencanaan | RPJMD, Renstra, Renja, RKPD, PK, Pohon Kinerja | `/rencana`, `/perbaiki` | ✅ susun/perbaiki | ✅ setujui | ✅ nilai keselarasan |
| Pengukuran | Rencana Aksi, capaian berkala | `/capaian` | ✅ pantau | ✅ pantau | ✅ verifikasi |
| Pelaporan | LKjIP/LKIP | `/laporan` | ✅ draft | ✅ reviu | ✅ nilai mutu |
| Evaluasi | LHE, LKE | `/nilai`, `/temuan` | ◑ baca | ◑ baca | ✅ evaluasi & temuan |
| Tindak lanjut | Rekomendasi & TL | `/temuan`(status) | ✅ tindaklanjuti | ✅ pantau | ✅ verifikasi TL |
| Tata kelola | (usulan agen) | `/perbaiki`,`/terapkan` | ◑ usul | ✅ terapkan | — |

---

## 6. Arsitektur teknis refactor

```
            Telegram
          ┌────┴─────┐
   /slash │          │ kalimat bahasa alami
          ▼          ▼
  bot/parser_slash   agent/nlu.parse (+ parse_llm fallback)
          └────┬─────┘
               ▼
        Permintaan  (dataclass: aksi, opd, tahun, periode, tahapan, dokumen, level, fokus)
               ▼
   bot/dispatcher.jalankan(permintaan, message, user)
     • resolusi OPD (cocokkan_opd: id/kode/nama/saya/semua)
     • cek RBAC (boleh_opd / boleh_promosi)  & default lingkup per-peran
     • default tahun/periode
               ▼
   _aksi_rencana · _aksi_capaian · _aksi_nilai · _aksi_laporan ·
   _aksi_temuan · _aksi_banding · _aksi_perbaiki · _aksi_dokumen …
               ▼
   agent/* (Dosir, evaluator, improver, analitik, llm)  +  db/profiles (esakip)
```

Komponen baru/refactor:
- **`agent/permintaan.py`** — dataclass `Permintaan` + enum slot (sumber kebenaran tata bahasa). `agent/nlu.Intent` dilebur ke sini (ditambah periode/tahapan/dokumen/level/fokus).
- **`bot/parser_slash.py`** — parser flag+posisional → `Permintaan`.
- **`bot/dispatcher.py`** — `jalankan()` tunggal; semua handler `/slash` (tipis) + `nl_handler` memanggilnya. Helper `_aksi_*` yang sudah diekstrak menjadi lapisan eksekusi.
- **Profil esakip** diperluas: pembaca dokumen (rpjmd/renstra/renja/pk/pohon/lkjip) + temuan/rekomendasi/TL + anggaran (untuk efisiensi).

---

## 7. Contoh end-to-end (slash & NL menghasilkan hal sama)

| Tujuan | Slash | Bahasa alami |
|---|---|---|
| Nilai LKE TW2 | `/nilai 1 thn=2026 tw=2` | "nilai AKIP opd 1 triwulan 2 2026" |
| Lihat PK eselon III | `/rencana 1 dok=pk level=unit` | "tampilkan PK eselon III dinas pendidikan" |
| Cek keselarasan | `/rencana 1 dok=pohon` | "cek keselarasan Renstra ke PK opd 1" |
| Draft analisis LKjIP | `/laporan 1 2026 dok=lkjip fokus=efisiensi` | "buatkan draft analisis efisiensi LKjIP opd 1" |
| Benchmark kabupaten | `/banding semua thn=2026` | "peringkat semua OPD 2026, rata-rata kabupaten" |
| Tindak lanjut | `/temuan 1 status=belum` | "rekomendasi yang belum ditindaklanjuti opd 1" |

---

## 8. Menu Telegram per peran (setMyCommands per scope)
- **Kasubbag Perencanaan:** `/rencana /capaian /perbaiki /laporan /nilai /temuan`
- **Kadis:** `/nilai /banding /laporan /perbaiki /terapkan /capaian`
- **Evaluator Kabupaten:** `/nilai /banding /temuan /rencana /capaian /dokumen`
- **Umum (semua):** `/mulai /bantuan /akun /opd`

---

## 9. Kompatibilitas mundur
- `/evaluasi` → alias `/nilai`; `/gap` → `/nilai` (fokus gap); `/tren`+`/benchmark` → `/banding`; `/usul`+`/usulan` → `/perbaiki`; `/status` → `/akun`; `/help` → `/bantuan`; `/start` → `/mulai`.
- Bentuk posisional lama (`/evaluasi 1 2026`) tetap valid.
- Alias didaftarkan agar pengguna lama tak terganggu, dengan pesan halus mengarahkan ke verba baru.

---

## 10. Rencana implementasi bertahap (rendah-risiko dulu) — STATUS

1. **R1 — Fondasi + translator aman:** `Permintaan` + dispatcher tunggal `_jalankan`; verba lama dialihkan; slot `periode/dokumen/level/fokus`; translator §3A (heuristik→LLM terstruktur→grounding), peta‑error sopan, klarifikasi + `sakipgen_nlu_total`. ✅ **Selesai**.
2. **R2 — Pengukuran & dokumen:** `/capaian` per periode (`ambil_capaian` + `_PERIODE_DB`) ✅; `/dokumen` nyata — `agent/dokumen.py` + `profil.ambil_dokumen` (dokumen+versi+bukti), `_aksi_dokumen` ✅. + uji.
3. **R3 — Perencanaan kaya:** `/rencana` sadar-dokumen + keselarasan/cascading nyata via `sakip_cascading_relasi` (`agent/keselarasan.py` + `profil.ambil_cascading`, arah naik/turun). ✅ **Selesai**. + uji.
4. **R4 — Pelaporan & evaluasi internal:** `/laporan` (draft LKjIP via LLM, anti-halu) ✅ + `/temuan` (temuan→rekomendasi→TL via `profil.ambil_temuan`) ✅.
5. **R5 — Menu per peran + kalibrasi LKE 88/2021:** `bot/menu.py` setMyCommands per scope (default global + per-chat sesuai peran; dipasang saat startup & setelah /daftar) ✅; bobot evaluator dikalibrasi ke 88/2021 (Pengungkit 60 = 18/18/9/15 dari split AKIP 30/30/15/25; Hasil 40) ✅.

> Realisasi peran: enum nyata `operator`≈Kasubbag, `kepala_dinas`≈Kadis, `admin`≈Evaluator/Admin
> (Telegram tak punya scope "peran", maka menu peran dipasang per-chat privat pengguna).

---

## 11. Penegasan tata kelola (tetap)
- Semua angka **estimasi indikatif** — bukan LKE/Nilai AKIP resmi MenPAN-RB (disclaimer di setiap keluaran).
- Bot **read-only** ke sumber; satu-satunya tulisan resmi via `/terapkan` (manusia berwenang + optimistic-lock + audit sebelum→sesudah).
- `terapkan` **tidak** lewat bahasa alami.
