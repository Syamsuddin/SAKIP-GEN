# SPDX-License-Identifier: MIT
# SAKIP-Gen — Evaluator + Drafter untuk SAKIP PermenPAN-RB 88/2021
# Lihat LICENSE untuk detail MIT License.

"""Evaluator LKE SAKIP-Gen — model skoring terstruktur (heuristik transparan).

Struktur mengikuti semangat PermenPAN-RB 88/2021: dua kelompok komponen —
**Pengungkit (proses)** dan **Hasil** — dengan bobot default total 100:

  Pengungkit (60): Perencanaan 18, Pengukuran 18, Pelaporan 9, Evaluasi Internal 15
                   (= bobot AKIP baku 30/30/15/25 diskalakan ke envelope 60%)
  Hasil (40)     : Capaian Kinerja (dari persen capaian aktual)

Penting:
- "Pengukuran" menilai KELENGKAPAN/PROSES pengukuran (apakah diukur), sedangkan
  "Capaian Kinerja" menilai TINGKAT pencapaian aktual (realisasi vs target). Keduanya
  sengaja dipisah sesuai kerangka AKIP.
- Bobot adalah APPROKSIMASI yang DAPAT DIKALIBRASI ke instrumen LKE resmi via
  LKE_BOBOT (JSON). Skoring ini bukan LKE resmi — kalibrasi sebelum dipakai keputusan.
- Capaian mengasumsikan arah "maksimal" (realisasi/target, di-cap 100%). Arah minimal/
  stabil belum dimodelkan (lihat Dosir.Capaian) — penyempurnaan fase berikutnya.
"""
from __future__ import annotations

import json

from pydantic import BaseModel, Field

from agent.dosir import DosirKinerja
from config import get_settings

TIPOLOGI_HASIL = {"outcome", "impact"}

# Bobot default — kalibrasi ke PermenPAN-RB 88/2021: Pengungkit 60 + Hasil 40.
# Pembagian dalam Pengungkit memakai bobot komponen AKIP baku 30/30/15/25
# (Perencanaan/Pengukuran/Pelaporan/Evaluasi Internal) yang diskalakan ke envelope 60%:
#   Perencanaan 30%·0,6=18 · Pengukuran 30%·0,6=18 · Pelaporan 15%·0,6=9 · Eval Internal 25%·0,6=15.
# Hasil (Capaian Kinerja) = 40. Dapat dikalibrasi penuh via LKE_BOBOT (JSON).
BOBOT_DEFAULT: dict[str, float] = {
    "Perencanaan Kinerja": 18.0,
    "Pengukuran Kinerja": 18.0,
    "Pelaporan Kinerja": 9.0,
    "Evaluasi Akuntabilitas Kinerja Internal": 15.0,
    "Capaian Kinerja": 40.0,
}

# Kata pembuka rumusan yang menandakan orientasi OUTPUT (deteksi mislabel; T2.4).
_KATA_OUTPUT = (
    "jumlah", "tersedianya", "terlaksananya", "terselenggaranya",
    "terbangunnya", "tersusunnya", "terdistribusinya",
)


def get_bobot() -> dict[str, float]:
    """Bobot komponen aktif: BOBOT_DEFAULT di-override LKE_BOBOT (JSON) bila ada."""
    try:
        raw = get_settings().lke_bobot
    except Exception:  # noqa: BLE001 — settings belum siap → pakai default
        raw = None
    bobot = dict(BOBOT_DEFAULT)
    if raw:
        try:
            for k, v in json.loads(raw).items():
                if k in bobot:
                    bobot[k] = float(v)
        except (ValueError, TypeError):
            pass
    return bobot


class GapTemuan(BaseModel):
    komponen: str
    deskripsi: str
    estimasi_poin: float
    detail: list[str] = Field(default_factory=list)


class NilaiKomponen(BaseModel):
    nama: str
    bobot: float
    skor: float        # 0..100
    kontribusi: float  # skor * bobot / 100


class HasilEvaluasi(BaseModel):
    instansi: str
    tahun: int
    komponen: list[NilaiKomponen]
    nilai_total: float
    predikat: str
    keterangan_predikat: str
    gap: list[GapTemuan] = Field(default_factory=list)
    peringatan: list[str] = Field(default_factory=list)  # integritas data (T2.4)


def predikat_dari_nilai(nilai: float) -> tuple[str, str]:
    if nilai > 90:
        return "AA", "Sangat Memuaskan"
    if nilai > 80:
        return "A", "Memuaskan"
    if nilai > 70:
        return "BB", "Sangat Baik"
    if nilai > 60:
        return "B", "Baik"
    if nilai > 50:
        return "CC", "Cukup (Memadai)"
    if nilai > 30:
        return "C", "Kurang"
    return "D", "Sangat Kurang"


def _indikator(dosir: DosirKinerja):
    return [i for s in dosir.perencanaan.sasaran_strategis for i in s.indikator]


def _skor_perencanaan(dosir: DosirKinerja, bobot: float):
    ind = _indikator(dosir)
    if not ind:
        return 0.0, [GapTemuan(
            komponen="Perencanaan Kinerja",
            deskripsi="Belum ada sasaran/indikator kinerja yang terdefinisi.",
            estimasi_poin=round(bobot, 2),
        )]
    n = len(ind)
    n_hasil = sum(1 for i in ind if (i.tipologi or "") in TIPOLOGI_HASIL)
    skor = 40.0 + 60.0 * (n_hasil / n)
    gaps = []
    output_ind = [i for i in ind if (i.tipologi or "") not in TIPOLOGI_HASIL]
    if output_ind:
        delta = 60.0 * (1 - n_hasil / n)
        gaps.append(GapTemuan(
            komponen="Perencanaan Kinerja",
            deskripsi=f"{len(output_ind)} dari {n} indikator belum berorientasi hasil; rumuskan ulang ke outcome.",
            estimasi_poin=round(bobot / 100 * delta, 2),
            detail=[f"{i.indikator_id} — {i.uraian} (tipologi: {i.tipologi or 'tak diketahui'})" for i in output_ind],
        ))
    return round(skor, 2), gaps


def _skor_pengukuran(dosir: DosirKinerja, bobot: float):
    """Kelengkapan PROSES pengukuran (apakah target & realisasi tersedia)."""
    ind = _indikator(dosir)
    if not ind:
        return 0.0, []
    n = len(ind)
    terukur = {c.indikator_id for c in dosir.pengukuran.capaian
               if c.target is not None and c.realisasi is not None}
    m = sum(1 for i in ind if i.indikator_id in terukur)
    skor = 100.0 * m / n
    gaps = []
    if m < n:
        delta = 100.0 - skor
        gaps.append(GapTemuan(
            komponen="Pengukuran Kinerja",
            deskripsi=f"Data capaian (target & realisasi) belum lengkap untuk {n - m} dari {n} indikator.",
            estimasi_poin=round(bobot / 100 * delta, 2),
        ))
    return round(skor, 2), gaps


def _skor_capaian(dosir: DosirKinerja, bobot: float):
    """Komponen HASIL: tingkat pencapaian aktual (persen capaian, di-cap 100%)."""
    ind = _indikator(dosir)
    if not ind:
        return 0.0, [GapTemuan(
            komponen="Capaian Kinerja",
            deskripsi="Belum ada indikator untuk dinilai capaiannya.",
            estimasi_poin=round(bobot, 2),
        )]
    persen = {c.indikator_id: c.persen_capaian for c in dosir.pengukuran.capaian
              if c.persen_capaian is not None}
    nilai: list[float] = []
    belum: list = []
    rendah: list[tuple] = []
    for i in ind:
        p = persen.get(i.indikator_id)
        if p is None:
            nilai.append(0.0)
            belum.append(i)
        else:
            capped = min(float(p), 100.0)
            nilai.append(capped)
            if capped < 100.0:
                rendah.append((i, capped))
    skor = sum(nilai) / len(ind)
    gaps = []
    if skor < 100.0:
        detail = [f"{i.indikator_id} — {i.uraian} (capaian belum terukur)" for i in belum]
        detail += [f"{i.indikator_id} — {i.uraian} (capaian {c:.0f}%)"
                   for i, c in sorted(rendah, key=lambda t: t[1])[:5]]
        gaps.append(GapTemuan(
            komponen="Capaian Kinerja",
            deskripsi=f"Capaian kinerja rata-rata {skor:.0f}% dari target; tingkatkan realisasi/lengkapi data.",
            estimasi_poin=round(bobot / 100 * (100.0 - skor), 2),
            detail=detail,
        ))
    return round(skor, 2), gaps


def _skor_pelaporan(dosir: DosirKinerja, bobot: float):
    p = dosir.pelaporan
    skor = (50 if p.ada_lkjip else 0) + (30 if p.ada_analisis_capaian else 0) + (20 if p.ada_analisis_efisiensi else 0)
    miss = []
    if not p.ada_lkjip:
        miss.append(("Dokumen LKjIP/LKIP belum tersedia", 50))
    if not p.ada_analisis_capaian:
        miss.append(("Analisis capaian kinerja belum ada", 30))
    if not p.ada_analisis_efisiensi:
        miss.append(("Analisis efisiensi penggunaan anggaran belum ada", 20))
    gaps = []
    if miss:
        total = sum(poin for _, poin in miss)
        gaps.append(GapTemuan(
            komponen="Pelaporan Kinerja",
            deskripsi="Laporan kinerja belum lengkap atau belum analitis.",
            estimasi_poin=round(bobot / 100 * total, 2),
            detail=[m for m, _ in miss],
        ))
    return float(skor), gaps


def _skor_evaluasi_internal(dosir: DosirKinerja, bobot: float):
    e = dosir.evaluasi_internal
    skor = (60 if e.ada_evaluasi_internal else 0) + (40 if e.ada_tindak_lanjut else 0)
    miss = []
    if not e.ada_evaluasi_internal:
        miss.append(("Evaluasi internal (APIP) belum dilakukan", 60))
    if not e.ada_tindak_lanjut:
        miss.append(("Tindak lanjut rekomendasi belum ada", 40))
    gaps = []
    if miss:
        total = sum(poin for _, poin in miss)
        gaps.append(GapTemuan(
            komponen="Evaluasi Akuntabilitas Kinerja Internal",
            deskripsi="Evaluasi akuntabilitas internal belum optimal.",
            estimasi_poin=round(bobot / 100 * total, 2),
            detail=[m for m, _ in miss],
        ))
    return float(skor), gaps


def _peringatan_integritas(dosir: DosirKinerja) -> list[str]:
    """T2.4 — tandai indikator berlabel outcome/impact tetapi rumusannya berbau output."""
    w: list[str] = []
    for i in _indikator(dosir):
        u = (i.uraian or "").strip().lower()
        if (i.tipologi or "") in TIPOLOGI_HASIL and u.startswith(_KATA_OUTPUT):
            w.append(
                f"{i.indikator_id} dilabeli '{i.tipologi}' tetapi rumusannya berorientasi "
                f"output ('{i.uraian}') — perlu verifikasi."
            )
    return w


def evaluasi_lke(dosir: DosirKinerja, bobot: dict[str, float] | None = None) -> HasilEvaluasi:
    bobot = bobot or get_bobot()
    fungsi = [
        ("Perencanaan Kinerja", _skor_perencanaan),
        ("Pengukuran Kinerja", _skor_pengukuran),
        ("Pelaporan Kinerja", _skor_pelaporan),
        ("Evaluasi Akuntabilitas Kinerja Internal", _skor_evaluasi_internal),
        ("Capaian Kinerja", _skor_capaian),
    ]
    komponen: list[NilaiKomponen] = []
    semua_gap: list[GapTemuan] = []
    for nama, fn in fungsi:
        b = bobot.get(nama, 0.0)
        skor, gaps = fn(dosir, b)
        komponen.append(NilaiKomponen(nama=nama, bobot=b, skor=skor,
                                      kontribusi=round(skor * b / 100, 2)))
        semua_gap.extend(gaps)
    nilai_total = round(sum(k.kontribusi for k in komponen), 2)
    kode, ket = predikat_dari_nilai(nilai_total)
    semua_gap.sort(key=lambda g: g.estimasi_poin, reverse=True)
    return HasilEvaluasi(
        instansi=dosir.meta.instansi, tahun=dosir.meta.tahun,
        komponen=komponen, nilai_total=nilai_total,
        predikat=kode, keterangan_predikat=ket, gap=semua_gap,
        peringatan=_peringatan_integritas(dosir),
    )
