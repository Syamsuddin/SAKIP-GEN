"""Analitik lanjutan (Fase 5): tren antar-tahun, benchmark antar-OPD, keselarasan
sasaran↔indikator, dan deteksi indikator berisiko. Logika inti murni (tanpa I/O)
agar mudah diuji; pembungkus `tren_opd`/`benchmark_opd` menarik data via evaluasi_opd.
"""
from __future__ import annotations

from agent.dosir import DosirKinerja
from agent.evaluator import TIPOLOGI_HASIL, HasilEvaluasi


# ---------- T5.2: tren antar-tahun ----------
def delta_nilai(kini: HasilEvaluasi, lalu: HasilEvaluasi) -> dict:
    """Selisih nilai total & per komponen (kini − lalu)."""
    skor_lalu = {k.nama: k.skor for k in lalu.komponen}
    per_komponen = {
        k.nama: round(k.skor - skor_lalu.get(k.nama, 0.0), 2) for k in kini.komponen
    }
    return {"total": round(kini.nilai_total - lalu.nilai_total, 2), "komponen": per_komponen}


async def tren_opd(opd_id: int, tahun: int, tahun_lalu: int | None = None):
    """Evaluasi satu OPD untuk `tahun` dan `tahun_lalu` (default tahun−1) + delta."""
    from agent.service import evaluasi_opd

    tahun_lalu = tahun_lalu or (tahun - 1)
    _, kini = await evaluasi_opd(opd_id, tahun)
    _, lalu = await evaluasi_opd(opd_id, tahun_lalu)
    return kini, lalu, delta_nilai(kini, lalu)


# ---------- T5.2: benchmark antar-OPD ----------
def peringkat(items: list[tuple[str, float]]) -> list[tuple[int, str, float]]:
    """(label, nilai) → (rank, label, nilai) urut nilai menurun (rank mulai 1)."""
    urut = sorted(items, key=lambda t: t[1], reverse=True)
    return [(i + 1, label, nilai) for i, (label, nilai) in enumerate(urut)]


async def benchmark_opd(opd_ids: list[int], tahun: int) -> list[tuple[int, str, float]]:
    """Peringkat nilai total beberapa OPD pada satu tahun (OPD gagal-evaluasi dilewati)."""
    from agent.service import evaluasi_opd

    hasil: list[tuple[str, float]] = []
    for oid in opd_ids:
        try:
            _, h = await evaluasi_opd(oid, tahun)
        except Exception:  # noqa: BLE001 — lewati OPD bermasalah
            continue
        hasil.append((h.instansi, h.nilai_total))
    return peringkat(hasil)


# ---------- T5.3: keselarasan sasaran↔indikator (cascading ringkas) ----------
def keselarasan_sasaran(dosir: DosirKinerja) -> list[str]:
    """Sasaran yang BELUM punya indikator berorientasi hasil (outcome/impact) — tak selaras.

    Cascading vertikal lintas-dokumen (RPJMD→Renstra→Renja→PK) menyusul; ini mengecek
    keselarasan sasaran↔IKU pada satu Dosir.
    """
    w: list[str] = []
    for s in dosir.perencanaan.sasaran_strategis:
        if s.indikator and not any((i.tipologi or "") in TIPOLOGI_HASIL for i in s.indikator):
            w.append(f"Sasaran '{s.kode} — {s.uraian}' belum memiliki indikator outcome/impact.")
    return w


# ---------- T5.4: indikator berisiko (capaian rendah) ----------
def indikator_berisiko(dosir: DosirKinerja, ambang: float = 75.0) -> list[str]:
    """Indikator dengan persen capaian < `ambang` (untuk peringatan dini push triwulanan)."""
    nama = {
        i.indikator_id: i.uraian
        for s in dosir.perencanaan.sasaran_strategis for i in s.indikator
    }
    out: list[tuple[float, str]] = []
    for c in dosir.pengukuran.capaian:
        if c.persen_capaian is not None and c.persen_capaian < ambang:
            out.append((c.persen_capaian,
                        f"{c.indikator_id} — {nama.get(c.indikator_id, c.indikator_id)}: "
                        f"capaian {c.persen_capaian:.0f}% (< {ambang:.0f}%)"))
    return [teks for _, teks in sorted(out)]
