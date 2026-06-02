# Review Core Business: Kesesuaian SAKIP-Gen dengan SAKIP

> Tinjauan terhadap inti bisnis sistem — **SAKIP** (Sistem Akuntabilitas Kinerja Instansi
> Pemerintah). Menilai seberapa setia model, skoring, dan alur kerja SAKIP-Gen terhadap kerangka
> SAKIP/Evaluasi AKIP (PermenPAN-RB 88/2021) dan praktik pemerintah daerah. Tanggal: 2026-06-02.

Berbeda dari [REVIEW_KECERDASAN.md](REVIEW_KECERDASAN.md) (kualitas algoritma) dan
[REVIEW_TEKNOLOGI.md](REVIEW_TEKNOLOGI.md) (kematangan stack), dokumen ini menilai **kebenaran
domain**: apakah yang dihitung & disarankan sistem benar-benar mencerminkan bagaimana SAKIP
dinilai dan dijalankan.

> Catatan: rujukan regulatif di bawah bersifat umum; **instrumen LKE resmi direvisi berkala**.
> Verifikasi bobot/sub-aspek terhadap LKE & pedoman teknis terbaru sebelum dijadikan acuan.

---

## 1. Siklus SAKIP vs cakupan SAKIP-Gen

Siklus SAKIP penuh (PP 29/2014, PermenPAN-RB 53/2014):

| Tahap SAKIP | Artefak utama | Ditangani SAKIP-Gen? |
|---|---|---|
| **Perencanaan Kinerja** | RPJMD → Renstra → Renja → Perjanjian Kinerja (PK), IKU, pohon kinerja/cascading | ⚠️ Sebagian — membaca sasaran+indikator; **drafting** perbaikan indikator. Tidak menyusun/menyelaraskan PK/Renstra/pohon kinerja |
| **Pengukuran Kinerja** | Target vs realisasi, berkala (triwulanan) | ⚠️ Membaca capaian, tapi **tidak menilai capaian** (lihat §3) |
| **Pelaporan Kinerja** | LKjIP/LKIP | ❌ Hanya cek flag keberadaan; tidak menyusun/menganalisis LKjIP |
| **Evaluasi Kinerja** | Internal (APIP) + eksternal (MenPAN-RB) | ⚠️ Simulasi skoring approksimatif; bukan LKE resmi |

**Kesimpulan cakupan:** secara jujur, SAKIP-Gen bukan alat siklus-SAKIP penuh. Ia adalah
**"evaluator kualitas indikator + drafter rumusan outcome"** dengan simulasi nilai. Penamaan
"Evaluasi SAKIP" pada output bot ([bot/format.py:8](../bot/format.py#L8)) menyiratkan cakupan yang
lebih luas daripada yang sebenarnya disediakan — ini perlu dijernihkan (lihat §5).

---

## 2. Yang DITANGKAP dengan tepat (kekuatan domain)

Beberapa keputusan domain di sini justru **tajam dan relevan**:

1. **Fokus output→outcome menyasar masalah SAKIP #1 yang sebenarnya.** Temuan paling kronis &
   berulang dalam evaluasi AKIP pemda adalah *"indikator masih berorientasi output/proses, belum
   outcome."* Menjadikan ini inti drafter ([agent/improver.py](../agent/improver.py)) menunjukkan
   pemahaman domain yang benar — ini bukan fitur asal, melainkan menyerang akar persoalan.
2. **Tipologi rantai nilai (input/proses/output/outcome/impact)** dimodelkan tepat
   ([agent/dosir.py:24](../agent/dosir.py#L24)) — ini konsep *logic model* kinerja yang sahih.
3. **Rentang predikat AA–D sesuai ketentuan resmi.** Ambang `predikat_dari_nilai`
   ([agent/evaluator.py:48-61](../agent/evaluator.py#L48-L61)) — AA(>90), A(>80), BB(>70), B(>60),
   CC(>50), C(>30), D — selaras kategori dan keterangan resmi (Sangat Memuaskan … Sangat Kurang).
4. **Gap berprioritas + estimasi kenaikan nilai** sangat relevan secara kelembagaan: predikat AKIP
   berdampak nyata (reputasi, insentif/tunjangan, pertimbangan alokasi) sehingga OPD memang
   beroperasi dengan target menaikkan predikat — alat yang menunjuk "perbaikan termahal duluan"
   bermanfaat praktis.
5. **Kadens triwulanan** ([bot/scheduler.py:38-43](../bot/scheduler.py#L38-L43): 1 Jan/Apr/Jul/Okt)
   selaras irama pengukuran kinerja berkala.
6. **Prinsip tata kelola selaras semangat SAKIP**: keputusan & pencatatan resmi tetap di tangan
   manusia, agen hanya membaca + mendraft, semua perubahan teraudit. Ini sesuai realitas bahwa
   revisi indikator/PK harus melalui persetujuan pimpinan, bukan diubah otomatis oleh alat.

---

## 3. Divergensi domain utama (kelemahan terhadap SAKIP)

### 3.1 🔴 Komponen Hasil (capaian) hilang — inversi semangat 88/2021

Evaluasi AKIP per PermenPAN-RB 88/2021 menggeser tekanan **ke arah hasil**: secara garis besar
**Komponen Pengungkit/Proses (~60%)** + **Komponen Hasil (~40%)** (capaian kinerja organisasi &
akuntabilitas keuangan). SAKIP-Gen **hanya memodelkan sisi proses** lalu menormalkannya ke 100%,
dan **tidak menilai capaian aktual sama sekali**:

- Komponen "Pengukuran" hanya menghitung **kelengkapan data** (apakah `target` & `realisasi`
  terisi), bukan tingkat capaian ([agent/evaluator.py:92-109](../agent/evaluator.py#L92-L109)).
  `persen_capaian` dihitung tapi tak dipakai.
- Akibatnya: OPD dengan dokumen lengkap & data terisi bisa meraih nilai tinggi **meski realisasi
  kinerjanya 0%**. Ini **membalik** justru tujuan reformasi 88/2021 yang menekankan hasil/outcome.

### 3.2 🟠 Hanya menilai "Pemenuhan", bukan "Kualitas" & "Pemanfaatan"

LKE 88/2021 menilai tiap komponen pengungkit pada tiga lapis: **Pemenuhan** (ada/tidak),
**Kualitas** (mis. LKjIP analitis, indikator SMART), dan **Pemanfaatan** (data dipakai untuk
keputusan/efisiensi anggaran). SAKIP-Gen hanya menyentuh lapis **Pemenuhan** via flag boolean
([agent/evaluator.py:112-151](../agent/evaluator.py#L112-L151)) — tak bisa menilai apakah LKjIP
bermutu atau datanya dimanfaatkan.

### 3.3 🟠 Bobot tidak selaras instrumen resmi

Bobot sistem **30/30/15/25** ([agent/evaluator.py:16-21](../agent/evaluator.py#L16-L21)) tidak
cocok dengan 12/2015 (30/25/15/10 + Capaian 20) maupun struktur 60/40 pada 88/2021. Docstring jujur
menyebut ini "approksimasi", tapi konsumen bisa salah anggap sebagai nilai resmi.

### 3.4 🟠 Cascading / pohon kinerja & keselarasan tidak dievaluasi

SAKIP menuntut keselarasan RPJMD→Renstra→Renja→PK dan cascading antar-eselon. Field `level`
(dinas/bidang/seksi) ada di `UsulanPerbaikan` ([agent/usulan.py:28](../agent/usulan.py#L28)) tetapi
**evaluator mengabaikannya** — penilaian murni di tingkat OPD, tanpa memeriksa keselarasan
vertikal/horizontal indikator.

### 3.5 PK/Renstra/Renja sebagai dokumen tidak dimodelkan

Sistem membaca `sasaran_strategis + indikator + capaian` (mendekati isi PK), tetapi tidak memodelkan
dokumen PK/Renstra atau konsistensi internalnya (mis. apakah indikator PK selaras Renstra).

---

## 4. Risiko terhadap kredibilitas SAKIP (paling penting bagi core business)

### 4.1 🔴 Risiko misinterpretasi nilai

Output bot menampilkan **"Nilai total: 85.00 — Predikat: A — Memuaskan"** **tanpa peringatan apa
pun** bahwa ini approksimasi ([bot/format.py:7-19](../bot/format.py#L7-L19)). Disclaimer hanya ada
di docstring/dokumen, **tidak di pesan yang dilihat pengguna**. Karena skor sistematis
**melebih-lebihkan kepatuhan administratif** (§3.1), OPD bisa membentuk *false confidence*: merasa
"sudah A" padahal mengabaikan ~40% kerangka riil (hasil).

### 4.2 🔴 Moral hazard / gaming

Skor naik dengan: (a) **melabeli** indikator "outcome", (b) **mengisi** target+realisasi apa pun,
(c) **mencentang** flag pelaporan. Ketiganya bisa dimanipulasi tanpa memperbaiki akuntabilitas
nyata — relabel output jadi outcome, isi realisasi sembarang, set flag. Tanpa pengaman, alat ini
berisiko **mendorong kepatuhan kosmetik** — justru anti-pola yang diperangi reformasi SAKIP.

### 4.3 🟠 Penerapan langsung ke sumber dapat memutus keselarasan

`/terapkan` mengubah `indikator` sumber atas persetujuan kadis ([bot/kinerja.py:230-254](../bot/kinerja.py#L230-L254)).
Revisi indikator/PK nyata melibatkan Bappeda/TAPD/APIP dan harus menjaga konsistensi cascading
(Renstra/RPJMD). Audit menjaga *akuntabilitas* perubahan, tetapi tidak menjamin *konsistensi
substantif* dengan dokumen perencanaan di atasnya.

---

## 5. Penilaian & rekomendasi domain

**Penilaian:** Sebagai *produk SAKIP*, sistem ini **diagnosisnya tepat tetapi cakupan & skoringnya
parsial** (⭐⭐⭐). Ia menyasar persoalan paling nyata (orientasi outcome) dan menghormati prinsip
akuntabilitas-manusia SAKIP — itu kekuatan sejati. Namun ia **menilai proses, bukan hasil**, dan
menyajikan nilai yang dapat disalahartikan sebagai AKIP resmi. Kredibilitas, bukan teknologi, yang
menjadi taruhan utama.

| Prioritas | Rekomendasi | Alasan domain |
|---|---|---|
| 🔴 Tinggi | **Tambahkan disclaimer di output bot** ("estimasi internal, bukan hasil LKE resmi") | Cegah false confidence & misinterpretasi |
| 🔴 Tinggi | **Reposisi label**: sebut "Indeks Kualitas Implementasi SAKIP (proses)" — bukan "Nilai/Predikat AKIP" — selama Komponen Hasil belum ada | Jujur soal apa yang diukur |
| 🔴 Tinggi | **Nilai capaian aktual** (pakai `persen_capaian`) & rancang **Komponen Hasil** | Selaraskan dengan semangat 88/2021 |
| 🟠 Sedang | **Kalibrasi bobot & tiga sub-aspek** (Pemenuhan/Kualitas/Pemanfaatan) ke LKE 88/2021 terbaru | Validitas skoring |
| 🟠 Sedang | **Pengaman anti-gaming**: tandai indikator yang dilabeli outcome tapi `uraian` masih berbunyi output; minta bukti untuk flag pelaporan | Lindungi integritas |
| 🟠 Sedang | **Manfaatkan `level`**: evaluasi keselarasan/cascading antar-eselon | Kelengkapan domain |
| 🟢 Rendah | Perluas drafting ke gap pengukuran/pelaporan; monitoring target berisiko di push triwulanan | Cakupan siklus lebih utuh |

---

## Kesimpulan

Secara **core business SAKIP**, kekuatan terbesar SAKIP-Gen adalah **ketepatan sasaran** (outcome
orientation) dan **kesetiaan pada prinsip tata kelola** (human-in-the-loop, audit, sumber tunggal
kebenaran) — keduanya benar-benar selaras dengan jiwa SAKIP. Kelemahan terbesarnya adalah
**parsialitas**: ia mengukur *ketertiban proses* dan menyebutnya nilai AKIP, sementara komponen
**hasil/capaian** — inti reformasi PermenPAN-RB 88/2021 — belum dinilai.

Untuk menjadi produk SAKIP yang kredibel, dua hal harus didahulukan dan keduanya **tentang
kejujuran nilai, bukan kecanggihan**: (1) jangan sajikan angka proses sebagai "Nilai AKIP" tanpa
peringatan, dan (2) masukkan capaian hasil ke dalam penilaian. Tanpa itu, sistem berisiko — secara
tak sengaja — memperkuat kepatuhan administratif yang justru ingin dikoreksi oleh SAKIP.
