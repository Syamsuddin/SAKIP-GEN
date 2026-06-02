"""Pemformat hasil evaluasi untuk pesan Telegram (HTML).

Sejak Fase 2 nilai mencakup komponen Hasil (Capaian), sehingga total mendekati
struktur AKIP. Tetap disajikan sebagai ESTIMASI INTERNAL (indikatif) dengan disclaimer —
bobot perlu dikalibrasi ke instrumen LKE resmi dan ini bukan penilaian MenPAN-RB.
"""
from __future__ import annotations

from agent.evaluator import HasilEvaluasi

LABEL_NILAI = "Estimasi Nilai AKIP (indikatif)"

DISCLAIMER = (
    "ℹ️ <i>Estimasi internal SAKIP-Gen (bobot perlu kalibrasi LKE) — "
    "bukan hasil LKE/Nilai AKIP resmi MenPAN-RB. Alat bantu, bukan dasar keputusan resmi.</i>"
)


def _peringatan(hasil: HasilEvaluasi) -> list[str]:
    if not hasil.peringatan:
        return []
    baris = ["", "⚠️ <b>Integritas data</b>:"]
    baris += [f"• {p}" for p in hasil.peringatan[:3]]
    return baris


def format_ringkasan(hasil: HasilEvaluasi) -> str:
    baris = [f"<b>{LABEL_NILAI} — {hasil.instansi}</b>", f"Tahun {hasil.tahun}", ""]
    for k in hasil.komponen:
        baris.append(
            f"• {k.nama}: <b>{k.skor:.0f}</b>  (bobot {k.bobot:.0f}, kontrib {k.kontribusi:.1f})"
        )
    baris += [
        "",
        f"Estimasi nilai AKIP: <b>{hasil.nilai_total:.2f}</b>",
        f"Predikat (indikatif): <b>{hasil.predikat}</b> — {hasil.keterangan_predikat}",
    ]
    if hasil.gap:
        g = hasil.gap[0]
        baris += [
            "",
            f"Gap teratas: {g.deskripsi} (+{g.estimasi_poin})",
            "Ketik /gap untuk rinciannya.",
        ]
    baris += _peringatan(hasil)
    baris += ["", DISCLAIMER]
    return "\n".join(baris)


def format_gap(hasil: HasilEvaluasi) -> str:
    if not hasil.gap:
        return (
            f"Tidak ada gap signifikan untuk {hasil.instansi} ({hasil.tahun}).\n\n{DISCLAIMER}"
        )
    baris = [f"<b>Gap prioritas — {hasil.instansi} ({hasil.tahun})</b>", ""]
    for i, g in enumerate(hasil.gap, 1):
        baris.append(f"{i}. <b>+{g.estimasi_poin}</b> — {g.deskripsi}")
        baris.append(f"   <i>{g.komponen}</i>")
        for d in g.detail:
            baris.append(f"   – {d}")
    from agent.improver import saran_lanjutan
    saran = saran_lanjutan(hasil)
    if saran:
        baris += ["", "<b>Saran perbaikan</b>:"]
        baris += [f"• {x}" for x in saran]
    baris += _peringatan(hasil)
    baris += ["", DISCLAIMER]
    return "\n".join(baris)
