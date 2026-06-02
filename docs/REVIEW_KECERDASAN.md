# Review Kecerdasan SAKIP-Gen

> Penilaian terhadap tiga kemampuan inti — **analisis, drafting, dan evaluasi** — atas data
> SAKIP yang berada di MySQL. Tanggal review: 2026-06-02.

Penilaian ini menelaah kode di [agent/evaluator.py](../agent/evaluator.py),
[agent/improver.py](../agent/improver.py), [agent/llm.py](../agent/llm.py), dan
[db/queries.py](../db/queries.py).

Ringkasan jujur di depan: **SAKIP-Gen saat ini adalah sistem heuristik berbasis aturan yang
transparan dan tertata rapi, bukan sistem ber-AI yang benar-benar "memahami" SAKIP.** LLM hanya
menyentuh satu titik kecil (penghalusan kalimat usulan), dan itu pun opsional + best-effort.
Kecerdasannya terletak pada *rekayasa aturan*, bukan pada *penalaran model*.

---

## 1. Evaluasi LKE — ⭐⭐⭐ (struktur baik, substansi dangkal)

Evaluator memetakan empat komponen berbobot 30/30/15/25 dengan predikat AA–D. Logikanya
transparan dan dapat diaudit — itu kekuatan tata kelola yang nyata. Tetapi sebagai *penilaian
kinerja*, ada beberapa keterbatasan substansial:

**Temuan kritis — komponen Pengukuran mengabaikan capaian aktual.**
Di `_skor_pengukuran` ([agent/evaluator.py:92-109](../agent/evaluator.py#L92-L109)), skor hanya
menghitung **kelengkapan data** (apakah `target` dan `realisasi` terisi):

```python
terukur = {c.indikator_id for c in dosir.pengukuran.capaian
           if c.target is not None and c.realisasi is not None}
skor = 100.0 * m / n
```

Artinya: OPD yang mengisi target & realisasi untuk semua indikator mendapat **30 poin penuh —
meskipun realisasinya 0%.** Nilai `persen_capaian` sudah dihitung di
[db/queries.py:58-61](../db/queries.py#L58-L61) tetapi **tidak pernah dipakai** dalam skoring.
Ini lubang substansi terbesar: sistem menilai *ketertiban administrasi pengisian*, bukan
*tingkat kinerja*.

**Komponen Perencanaan bergantung penuh pada label `tipologi` di MySQL.**
`_skor_perencanaan` ([agent/evaluator.py:68-89](../agent/evaluator.py#L68-L89)) menilai dari
rasio indikator bertipologi `outcome/impact`. Tidak ada pemeriksaan apakah indikator yang
*dilabeli* "outcome" benar-benar outcome secara semantik. Jika data di MySQL salah label (atau
kolom `tipologi` kosong), seluruh penilaian Perencanaan jadi tidak valid. Tidak ada lapisan
verifikasi cerdas.

**Pelaporan & Evaluasi Internal hanyalah flag boolean.**
`_skor_pelaporan` ([agent/evaluator.py:112-131](../agent/evaluator.py#L112-L131)) membaca lima
boolean dari tabel `pelaporan_meta` (`ada_lkjip`, `ada_analisis_capaian`, …). Sistem **tidak
membaca dokumen LKjIP**, tidak menilai mutu analisis — hanya percaya pada flag yang (tampaknya)
diisi manual. Jadi "evaluasi" di sini = "apakah seseorang mencentang kotak", bukan penilaian isi.

**Yang tidak ada sama sekali:** analisis tren antar-tahun, perbandingan antar-OPD, sub-komponen
LKE yang sebenarnya (rubrik resmi punya puluhan butir), dan kalibrasi terhadap rubrik LKE
PermenPAN-RB 88/2021. Docstring sendiri jujur menyebut ini "APPROKSIMASI yang perlu dikalibrasi".

---

## 2. Analisis Gap — ⭐⭐⭐ (prioritisasi bagus, diagnosis mekanis)

Gap diturunkan langsung dari fungsi skoring dan diurutkan menurun berdasarkan `estimasi_poin`
([agent/evaluator.py:171](../agent/evaluator.py#L171)). **Prioritisasi berbasis estimasi kenaikan
nilai ini adalah fitur paling cerdas dalam sistem** — pengguna langsung tahu perbaikan mana yang
paling berdampak pada nilai.

Namun analisisnya **mekanis, bukan diagnostik**: gap hanya menyatakan *boolean mana yang hilang*
atau *berapa indikator yang belum outcome*. Tidak ada akar masalah ("mengapa indikator ini
output?"), tidak ada konteks sasaran strategis, tidak ada rekomendasi kontekstual per-OPD.
Estimasi poin juga mengasumsikan model linear sederhana (60/n untuk perencanaan) yang tidak
mencerminkan rubrik nyata.

---

## 3. Drafting Usulan — ⭐⭐ (titik terlemah)

Ini area dengan ruang perbaikan terbesar.

**Inti drafting masih manipulasi string.** `_rumusan_outcome`
([agent/improver.py:27-37](../agent/improver.py#L27-L37)):

```python
if low.startswith("jumlah"):
    return f"Persentase {sisa} yang memenuhi standar", "persen"
...
return f"Tingkat pemenuhan {low}", "persen"
```

"Jumlah sekolah terakreditasi" → "Persentase sekolah terakreditasi yang memenuhi standar". Pola
ini rapuh, generik, dan kadang menghasilkan kalimat janggal. Tidak ada pemahaman bahwa outcome
seharusnya mengukur *manfaat bagi masyarakat*, bukan sekadar mengubah "Jumlah" jadi "Persentase".

**LLM tersedia tapi perannya sangat dangkal:**
- Hanya menghaluskan field `uraian`
  ([agent/improver.py:87-101](../agent/improver.py#L87-L101)), tidak menyentuh logika usulan.
- Prompt single-shot tanpa contoh (few-shot), tanpa konteks **sasaran strategis** yang menaungi
  indikator ([agent/llm.py:21-27](../agent/llm.py#L21-L27)) — padahal outcome yang baik harus
  selaras dengan sasaran. Kualitas hasil pasti generik.
- Best-effort: semua kegagalan ditelan, fallback ke heuristik — bagus untuk keandalan, tapi
  berarti kualitas drafting tak terjamin.

**Cakupan drafting sangat sempit.** Hanya tipe `perbaikan_indikator` (output→outcome). Tidak ada
draft untuk gap **pengukuran** (cara melengkapi data capaian), **pelaporan** (menyusun
LKjIP/analisis), atau **evaluasi internal** — padahal ketiganya juga menghasilkan gap. Penerapan
otomatis di [db/promote.py:104-107](../db/promote.py#L104-L107) pun menolak tipe lain.

---

## Hubungan dengan data MySQL

Kecerdasan sistem **berbanding lurus dengan kualitas data di MySQL** — dan ini risiko utama:

- **Garbage in, garbage out:** evaluasi sepenuhnya bergantung pada `tipologi` yang benar dan
  `pelaporan_meta` yang jujur. Tidak ada lapisan validasi/deteksi anomali.
- **Schema seam belum tentu cocok:** SQL di [db/queries.py](../db/queries.py) mengasumsikan skema
  referensi dan **wajib disesuaikan** ke skema SAKIP nyata sebelum angka apa pun bisa dipercaya.
- **Read-only murni** — secara tata kelola ini benar dan aman, tapi berarti agen tidak bisa
  memperkaya/menormalkan data; ia hanya membaca apa adanya.

---

## Rekomendasi prioritas

| Prioritas | Perbaikan | Dampak |
|---|---|---|
| 🔴 Tinggi | **Masukkan `persen_capaian` ke skor Pengukuran** — nilai kinerja, bukan sekadar kelengkapan data | Menutup lubang substansi terbesar |
| 🔴 Tinggi | **Validasi/kalibrasi terhadap rubrik LKE resmi** + sub-komponen sebenarnya | Membuat nilai layak dipakai |
| 🟠 Sedang | **Perkaya prompt LLM**: few-shot + konteks sasaran strategis + satuan | Drafting jauh lebih relevan |
| 🟠 Sedang | **Perluas drafting** ke gap pengukuran/pelaporan/evaluasi | Cakupan usulan utuh |
| 🟢 Rendah | Analisis tren antar-tahun & benchmark antar-OPD | Diagnosis lebih dalam |
| 🟢 Rendah | Deteksi mis-label `tipologi` via LLM (verifikasi semantik) | Mengurangi GIGO |

---

## Verdict

| Dimensi | Nilai | Catatan |
|---|---|---|
| **Evaluasi** | ⭐⭐⭐ | Struktur & transparansi kuat; substansi dangkal (abaikan capaian aktual, andalkan flag) |
| **Analisis** | ⭐⭐⭐ | Prioritisasi by-impact cerdas; diagnosis mekanis |
| **Drafting** | ⭐⭐ | Masih manipulasi string; LLM dangkal & cakupan sempit |
| **Tata kelola** | ⭐⭐⭐⭐⭐ | Human-in-the-loop, RO, 3-kredensial, audit — sangat matang |

**Kesimpulan:** SAKIP-Gen unggul sebagai *kerangka tata kelola* dan *asisten administratif
terstruktur* — aman, auditable, dan jujur soal keterbatasannya (docstring secara konsisten
menandai "heuristik"/"approksimasi"). Tetapi "kecerdasan" substantif untuk *menilai* dan
*menyusun* kinerja masih embrionik: ia mengukur ketertiban, bukan mutu, dan menulis usulan dengan
template, bukan penalaran. Untuk naik kelas dari *rule engine* menjadi *evaluator cerdas*, tiga
perbaikan merah di atas adalah prasyaratnya — terutama memasukkan capaian aktual ke skor dan
memberi LLM konteks yang memadai.
