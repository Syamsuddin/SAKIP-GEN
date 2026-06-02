# Analisa Sistem Abstraksi Data MySQL pada SAKIP-Gen

> Bagaimana SAKIP-Gen memisahkan logika domain dari MySQL: pola arsitektur, lapisan, jalur baca
> vs tulis, strategi portabilitas, dan titik rapuhnya. Tanggal review: 2026-06-02.

Berkas terkait: [db/engines.py](../db/engines.py), [db/queries.py](../db/queries.py),
[db/staging.py](../db/staging.py), [db/promote.py](../db/promote.py), [db/events.py](../db/events.py),
[agent/dosir.py](../agent/dosir.py), [agent/usulan.py](../agent/usulan.py), dan DDL di
[db/ddl/](../db/ddl/).

---

## Gambaran besar

Abstraksi data SAKIP-Gen dibangun di atas **empat keputusan arsitektural** yang saling menguatkan:

1. **Pemisahan kewenangan lewat tiga engine berkredensial berbeda** (bukan flag aplikasi).
2. **Anti-corruption layer**: skema fisik SAKIP tidak pernah bocor ke logika; semua diterjemahkan
   ke model domain Pydantic (Dosir / Usulan) di satu lapisan "seam".
3. **Pemisahan jalur baca dan tulis** (mirip CQRS) yang ditegakkan sampai ke level koneksi DB.
4. **Portabilitas SQLite↔MySQL** lewat SQL polos + nilai turunan dihitung di Python + stempel
   waktu sebagai string ISO-8601.

Hasilnya: kode evaluator/improver **tidak pernah melihat SQL, baris, atau koneksi** — mereka hanya
menerima objek `DosirKinerja` dan mengembalikan `HasilEvaluasi`/`UsulanPerbaikan`. SQL terkurung
seluruhnya di paket `db/`.

```
                    BACA (read model)                         TULIS (write model)
  ┌───────────────────────────────────────┐     ┌──────────────────────────────────────────┐
  MySQL sumber ──(sakip_ro: SELECT)──► db/queries.py        agent/* ──► db/staging.py ──(sakip_staging)──► ai_usulan
  (opd, indikator,                       │  (anti-corruption    (UsulanPerbaikan)                              │
   capaian, ...)                         │   layer / mapper)                                                   │
                                         ▼                                                                     ▼
                                  agent/dosir.py ◄── agent/evaluator.py        db/promote.py ──(sakip_promotor: UPDATE kolom)──► indikator
                                  (DosirKinerja,      agent/improver.py         (whitelist + optimistic lock + audit) ──────────► ai_audit
                                   model domain)
```

---

## Lapisan 1 — Engine & pemisahan kredensial ([db/engines.py](../db/engines.py))

Inti abstraksi koneksi. Tiga engine SQLAlchemy async **independen**, masing-masing dibuat **lazy**
(saat pertama dipakai) dan **dapat di-override** untuk uji:

| Engine | Kredensial | GRANT | Modul pemakai |
|---|---|---|---|
| `get_ro_engine` | `sakip_ro` | `SELECT` seluruh skema | [db/queries.py](../db/queries.py) |
| `get_staging_engine` | `sakip_staging` | `INSERT/SELECT/UPDATE` `ai_usulan` (+ `ai_event`) | [db/staging.py](../db/staging.py), [db/events.py](../db/events.py), auth SQL |
| `get_promote_engine` | `sakip_promotor` | `SELECT`+`UPDATE` **level kolom** `indikator`, `INSERT ai_audit` | [db/promote.py](../db/promote.py) |

**Mengapa ini abstraksi yang kuat:** prinsip *least privilege* ditegakkan oleh **server MySQL**,
bukan oleh `if` di aplikasi. Walau ada bug yang mencoba `UPDATE` lewat engine RO, MySQL menolak di
level GRANT (lihat [db/ddl/promote.sql](../db/ddl/promote.sql): promotor bahkan hanya boleh
`UPDATE(uraian,satuan,tipologi)` — kolom lain ditolak server). Ini *defense-in-depth* nyata, bukan
kosmetik.

**Pola teknis pendukung:**
- **Lazy init** (`global _engine; if None: create`) → Fase 0/1 + seluruh uji jalan tanpa MySQL;
  `DB_*_URL` hanya wajib saat engine benar-benar dipakai.
- **Dependency injection via setter** (`set_ro_engine`/`set_staging_engine`/`set_promote_engine`)
  → uji menyuntik satu engine SQLite untuk ketiga peran ([tests/test_fase4.py](../tests/test_fase4.py)).
- **Ketahanan koneksi**: `pool_pre_ping=True` (deteksi koneksi mati) + `pool_recycle=1800`
  (hindari `wait_timeout` MySQL).

---

## Lapisan 2 — Anti-corruption layer / mapper baca ([db/queries.py](../db/queries.py))

Ini **jantung abstraksi baca**. Fungsinya menerjemahkan skema relasional SAKIP → potongan model
domain `DosirKinerja`. Setiap tabel sumber dipetakan satu fungsi:

| Fungsi | Tabel sumber | Menghasilkan |
|---|---|---|
| `ambil_meta` | `opd` | `Meta` |
| `ambil_perencanaan` | `sasaran_strategis` ⋈ `indikator` | `Perencanaan` |
| `ambil_pengukuran` | `capaian_kinerja` ⋈ `indikator` | `Pengukuran` |
| `ambil_pelaporan` | `pelaporan_meta` | `Pelaporan` + `EvaluasiInternal` |
| `bangun_dosir` | (orkestrasi keempatnya) | `DosirKinerja` |

**Karakter abstraksi:**
- **SQL polos `text()` tanpa ORM.** Pilihan sadar: portabel lintas dialek, eksplisit, mudah
  dicocokkan ke skema nyata — dengan ongkos hilangnya type-safety kolom (salah nama kolom baru
  ketahuan saat runtime).
- **Normalisasi di batas**: `tipologi` di-*lowercase* dan string kosong → `None` tepat di mapper
  ([db/queries.py:83](../db/queries.py#L83)), sehingga model domain selalu bersih.
- **Nilai turunan dihitung di Python**, bukan di SQL: `persen_capaian` lewat `_persen()`
  ([db/queries.py:58-61](../db/queries.py#L58-L61)) — menjaga SQL tetap portabel & logika bisnis
  tetap teruji unit.
- **Resolusi referensi**: `resolve_opd_id()` menerima ID numerik *atau* kode OPD → fleksibilitas
  antarmuka tanpa membocorkan detail ke handler bot.

**Inilah "schema seam" yang berulang kali ditandai sebagai titik adaptasi.** Mengganti SAKIP-Gen
ke skema MySQL nyata = menulis ulang SQL di file ini (dan padanannya di `db/promote.py`), tanpa
menyentuh evaluator/improver sama sekali. Itu nilai utama abstraksi ini.

---

## Lapisan 3 — Model domain sebagai kontrak ([agent/dosir.py](../agent/dosir.py), [agent/usulan.py](../agent/usulan.py))

`DosirKinerja` (Pydantic) adalah **batas abstraksi sesungguhnya**. Di atas garis ini tidak ada
konsep "tabel"/"baris"/"koneksi" — hanya `Meta`, `Perencanaan`, `Indikator`, `Capaian`, dst.
Evaluator dan improver beroperasi murni pada struktur ini, sehingga:
- dapat diuji tanpa DB (cukup bangun objek Pydantic);
- bebas dari perubahan skema fisik;
- punya validasi tipe otomatis di titik masuk.

`UsulanPerbaikan` adalah kontrak arah sebaliknya — objek netral berisi `perubahan[]` (lama→usulan)
yang dirender ke Telegram **dan** Mini App dari satu sumber, lalu diserialkan ke staging.

---

## Lapisan 4 — Abstraksi tulis ke staging ([db/staging.py](../db/staging.py))

Satu-satunya tempat agen menulis. Pola yang dipakai adalah **hybrid dokumen-relasional**:

- Kolom `payload JSON` menyimpan **state kanonik** (`UsulanPerbaikan.model_dump_json()`).
- Sekumpulan kolom **denormalisasi & terindeks** (`opd_id`, `tahun`, `indikator_id`, `status`,
  `estimasi_poin`, `hash_data_lama`) menjadi *projection* untuk query/filter cepat — didukung
  indeks `idx_opd_tahun` & `idx_status` di [db/ddl/staging.sql](../db/ddl/staging.sql).

Saat baca (`ambil_usulan`), **payload adalah sumber kebenaran** (di-`model_validate_json`),
sementara `status`/`ditinjau_oleh` diambil dari kolom (otoritatif untuk siklus hidup). Saat
keputusan (`putuskan_usulan`), payload **diserialkan ulang** agar `status` di dalam JSON tetap
sinkron dengan kolom.

**Catatan teknis:** `daftar_usulan` memakai `bindparam(expanding=True)` untuk klausa `IN`
([db/staging.py:136](../db/staging.py#L136)) — cara yang benar dan portabel untuk parameter list.

Siklus hidup status: `draft → disetujui/ditolak → diterapkan`, ditegakkan oleh ENUM MySQL +
validasi di `terapkan_usulan`.

---

## Lapisan 5 — Promosi terkendali + kontrol konkurensi ([db/promote.py](../db/promote.py))

Jalur tulis paling sensitif — sekaligus contoh abstraksi paling kaya. `terapkan_usulan`:

1. Membaca usulan, men-deserialkan `payload` kembali ke objek domain.
2. Membaca kondisi indikator sumber **saat ini** dan menghitung ulang `hash_indikator`.
3. **Optimistic locking** ([agent/usulan.py:44-56](../agent/usulan.py#L44-L56)): bandingkan hash
   kini vs `hash_data_lama` yang tersimpan saat draft dibuat. Beda → **tolak** ("data telah
   berubah"). Ini mencegah *lost update* **tanpa memegang lock DB** sepanjang siklus
   baca→tinjau→setujui→terapkan yang bisa berhari-hari.
4. **Whitelist kolom** `{uraian, satuan, tipologi}` di level aplikasi — berlapis dengan GRANT
   kolom di level server.
5. Semua dalam **satu transaksi** (`eng.begin()`): UPDATE sumber + INSERT audit + tandai status.
6. **Idempoten-aman**: penerapan ulang ditolak karena status sudah `diterapkan`.

Hash sebagai *concurrency token* adalah pilihan elegan: ringan (SHA-256 atas 4 field), portabel,
dan tak bergantung kolom versi/timestamp di skema sumber.

---

## Lapisan pendukung — Event log dwi-sink ([db/events.py](../db/events.py))

Abstraksi audit aktivitas yang **best-effort & tak pernah melempar error**: selalu menulis ke
logger (journald), lalu mencoba INSERT ke `ai_event` lewat engine staging. Bila engine belum siap
atau insert gagal, dilewati dengan peringatan. Artinya jejak tak pernah jadi titik gagal kritis,
dan sistem inti tak bergantung pada ketersediaan tabel audit.

---

## Strategi portabilitas SQLite ↔ MySQL

Satu basis kode jalan di dua mesin DB — kunci kecepatan uji. Caranya:

| Teknik | Implementasi | Manfaat |
|---|---|---|
| SQL polos lintas-dialek | `text(...)` tanpa fitur khas vendor | Sama di SQLite & MySQL |
| Waktu sebagai string ISO-8601 UTC | `datetime.now(UTC).isoformat()` di seluruh `db/*` | Hindari beda tipe DATETIME/TEXT |
| Nilai turunan di Python | `_persen`, skoring di `agent/` | SQL tetap sederhana & teruji |
| Skema kembar | `*_SCHEMA_SQLITE` (Python) vs `.sql` (MySQL) | Uji menyemai SQLite; produksi pakai DDL |
| Engine overridable | `set_*_engine` + `StaticPool` SQLite in-memory | Uji deterministik tanpa MySQL |

Konsekuensinya, [demo_evaluasi.py](../demo_evaluasi.py) & tes Fase 4 menaruh tabel sumber **dan**
`ai_*` di **satu** SQLite untuk meniru satu MySQL.

---

## Pola arsitektur yang teridentifikasi

| Pola | Wujud di SAKIP-Gen |
|---|---|
| **Anti-Corruption Layer (DDD)** | `db/queries.py` melindungi domain dari skema SAKIP eksternal |
| **Repository / Data Mapper** | `db/queries.py`, `db/staging.py` memetakan baris ↔ model Pydantic |
| **CQRS (ringan)** | Jalur baca (RO→Dosir) terpisah total dari jalur tulis (domain→staging→promote), bahkan beda kredensial |
| **Hybrid dokumen-relasional** | `ai_usulan.payload (JSON)` + kolom denormalisasi terindeks |
| **Optimistic concurrency control** | `hash_indikator` sebagai *version token* |
| **Dependency Injection + Lazy init** | `get_*_engine` / `set_*_engine` |
| **Outbox/audit dwi-sink** | `db/events.py` (logger selalu, DB best-effort) |

---

## Titik rapuh & risiko

1. **Schema seam tersebar di dua file.** Pemetaan skema ada di [db/queries.py](../db/queries.py)
   (baca) **dan** [db/promote.py](../db/promote.py) (tulis, lihat `_SQL_INDIKATOR`/`_SQL_UPDATE_IND`).
   Saat menyesuaikan ke MySQL nyata, **keduanya** harus diubah konsisten — mudah terlewat.
2. **Tanpa type-safety kolom.** SQL string mentah → typo nama kolom hanya tertangkap saat
   runtime/uji, bukan saat lint/mypy.
3. **`bangun_dosir` membuka 4 koneksi terpisah** (satu per `ambil_*`), tanpa transaksi/ snapshot
   tunggal. Untuk SAKIP yang jarang berubah saat dibaca ini dapat diterima, tetapi secara teori
   bisa membaca data tak-konsisten antar sub-query. Optimasi mudah: bagikan satu `connection`.
4. **Duplikasi `status` (kolom vs payload).** Sinkron dijaga manual di `putuskan_usulan`; bila ada
   jalur tulis baru yang lupa menyinkronkan, payload bisa *drift* dari kolom.
5. **Asumsi ko-lokasi:** tabel `ai_*` diasumsikan **berada di skema `sakip` yang sama** dengan
   tabel sumber (promote menge-JOIN `ai_usulan` dengan `indikator`). Memisah staging ke DB lain
   akan memutus JOIN ini.
6. **Tanpa alat migrasi (Alembic).** DDL `.sql` diterapkan manual → risiko *drift* skema antar
   lingkungan; perubahan kolom `ai_*` tidak terversi.

---

## Penilaian & rekomendasi

**Penilaian:** Abstraksi data SAKIP-Gen **matang dan berprinsip** (⭐⭐⭐⭐). Ia menerapkan pola
kelas-enterprise (ACL, CQRS ringan, optimistic locking, least-privilege berbasis kredensial) pada
basis kode yang ringkas, dengan portabilitas uji yang sangat baik. Kekuatan terbesarnya bukan
performa, melainkan **keamanan & isolasi**: mustahil bagi logika agen menulis ke sumber kecuali
lewat jalur promosi yang teraudit dan dibatasi server.

**Rekomendasi (prioritas):**

| Prioritas | Tindakan | Alasan |
|---|---|---|
| 🔴 Tinggi | Saat adaptasi skema nyata, ubah `db/queries.py` **dan** `db/promote.py` bersamaan + tambah uji integrasi pemetaan | Seam ganda; salah satu terlewat = bug senyap |
| 🟠 Sedang | Bagikan satu koneksi RO di `bangun_dosir` (konsistensi baca + 1 round-trip) | Konsistensi & efisiensi |
| 🟠 Sedang | Pertimbangkan SQLAlchemy Core `Table`/`MetaData` (tetap tanpa ORM penuh) untuk memetakan kolom sekali → kurangi typo | Type-safety tanpa kehilangan kontrol SQL |
| 🟢 Rendah | Adopsi Alembic untuk migrasi tabel `ai_*` | Cegah drift skema |
| 🟢 Rendah | Jadikan `payload` satu-satunya sumber `status` saat baca (sudah), dan dokumentasikan kolom sebagai *projection read-only* | Hindari drift kolom↔payload |

**Kesimpulan:** sistem abstraksi data adalah **salah satu bagian terkuat** SAKIP-Gen. Yang
menentukan keberhasilan integrasi bukan kualitas abstraksinya — melainkan ketelitian menyesuaikan
*schema seam* ([db/queries.py](../db/queries.py) + [db/promote.py](../db/promote.py)) ke MySQL
SAKIP yang sebenarnya.
