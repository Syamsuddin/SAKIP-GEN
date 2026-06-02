"""Penyusun usulan perbaikan dari hasil evaluasi (Fase 3).

Saat ini berbasis heuristik transparan: indikator bertipologi output/proses/input
dirumuskan ulang menjadi outcome. Titik `_rumusan_outcome` adalah SAMBUNGAN LLM —
ganti dengan panggilan model (anthropic SDK / Ollama) untuk rumusan yang lebih baik.
Estimasi kenaikan nilai sejalan dengan evaluator: tiap indikator output yang diubah
ke outcome menaikkan sub-skor Perencanaan sebesar 60/n, berkontribusi
(bobot Perencanaan / 100) × 60/n (bobot terkalibrasi via get_bobot()).
"""
from __future__ import annotations

from agent.dosir import DosirKinerja, Indikator
from agent.evaluator import TIPOLOGI_HASIL, HasilEvaluasi, get_bobot
from agent.usulan import PerubahanField, UsulanPerbaikan, hash_indikator


def _indikator_list(dosir: DosirKinerja) -> list[Indikator]:
    return [i for s in dosir.perencanaan.sasaran_strategis for i in s.indikator]


def _cari(dosir: DosirKinerja, indikator_id: str) -> Indikator | None:
    for i in _indikator_list(dosir):
        if i.indikator_id == indikator_id:
            return i
    return None


def _rumusan_outcome(ind: Indikator) -> tuple[str, str | None]:
    """Heuristik rumusan ulang ke outcome. (SAMBUNGAN LLM ada di sini.)"""
    u = ind.uraian.strip()
    low = u.lower()
    if low.startswith("jumlah"):
        sisa = u[len("jumlah"):].strip()
        sisa = (sisa[:1].lower() + sisa[1:]) if sisa else "objek layanan"
        return f"Persentase {sisa} yang memenuhi standar", "persen"
    if low.startswith(("persentase", "indeks", "tingkat", "rasio")):
        return u, ind.satuan
    return f"Tingkat pemenuhan {low}", "persen"


def usulkan_perbaikan_indikator(
    dosir: DosirKinerja, hasil: HasilEvaluasi, indikator_id: str
) -> UsulanPerbaikan | None:
    """Susun usulan mengubah satu indikator output menjadi outcome. None bila tak relevan."""
    ind = _cari(dosir, indikator_id)
    if ind is None or (ind.tipologi or "") in TIPOLOGI_HASIL:
        return None
    n = len(_indikator_list(dosir)) or 1
    # Mengubah 1 indikator output→outcome menaikkan sub-skor Perencanaan sebesar 60/n;
    # kontribusi ≈ (bobot Perencanaan / 100) × 60/n. Selaras evaluator (bobot terkalibrasi).
    estimasi = round(get_bobot()["Perencanaan Kinerja"] / 100 * 60.0 / n, 2)
    uraian_baru, satuan_baru = _rumusan_outcome(ind)
    perubahan = [
        PerubahanField(field="uraian", lama=ind.uraian, usulan=uraian_baru),
        PerubahanField(field="tipologi", lama=ind.tipologi, usulan="outcome"),
    ]
    if satuan_baru and satuan_baru != ind.satuan:
        perubahan.append(PerubahanField(field="satuan", lama=ind.satuan, usulan=satuan_baru))
    return UsulanPerbaikan(
        instansi=hasil.instansi,
        opd_id=dosir.meta.opd_id,
        tahun=dosir.meta.tahun,
        indikator_id=ind.indikator_id,
        perubahan=perubahan,
        alasan=(
            "Indikator masih berorientasi output/proses. Rumuskan ulang ke outcome agar "
            "mengukur hasil/manfaat, sesuai sub-komponen Kualitas Perencanaan Kinerja (LKE)."
        ),
        gap_lke="Perencanaan Kinerja",
        estimasi_poin=estimasi,
        hash_data_lama=hash_indikator(ind),
    )


def usulkan_dari_gap(
    dosir: DosirKinerja, hasil: HasilEvaluasi, maksimal: int = 3
) -> list[UsulanPerbaikan]:
    """Hasilkan hingga `maksimal` usulan untuk indikator yang belum berorientasi hasil."""
    out: list[UsulanPerbaikan] = []
    for i in _indikator_list(dosir):
        if (i.tipologi or "") not in TIPOLOGI_HASIL:
            u = usulkan_perbaikan_indikator(dosir, hasil, i.indikator_id)
            if u is not None:
                out.append(u)
        if len(out) >= maksimal:
            break
    return out


async def sempurnakan_dengan_llm(usulan, *, sasaran=None, satuan=None, settings=None):
    """Perbaiki rumusan 'uraian' pada usulan memakai LLM bila tersedia (best-effort).

    Tidak mengubah `hash_data_lama` (yang berbasis data sumber lama), hanya nilai
    usulan. `sasaran`/`satuan` memperkaya konteks prompt (T3.3). Bila LLM tak
    tersedia/gagal, usulan dikembalikan apa adanya (heuristik).
    """
    from agent.llm import rumuskan_outcome

    pu = next((p for p in usulan.perubahan if p.field == "uraian"), None)
    if pu is None:
        return usulan
    baru = await rumuskan_outcome(
        pu.lama or "", satuan=satuan, tipologi="output", sasaran=sasaran, settings=settings
    )
    if baru:
        pu.usulan = baru
    return usulan


def cari_sasaran_indikator(dosir: DosirKinerja, indikator_id: str) -> str | None:
    """Uraian sasaran strategis yang menaungi sebuah indikator (untuk konteks LLM)."""
    for s in dosir.perencanaan.sasaran_strategis:
        if any(i.indikator_id == indikator_id for i in s.indikator):
            return s.uraian
    return None


# T3.5 — saran perbaikan ADVISORY untuk gap di luar perbaikan_indikator (tidak diterapkan
# otomatis; menjadi panduan manusia). Penerapan terstruktur tipe-tipe ini menyusul.
_SARAN_LANJUTAN = {
    "Pengukuran Kinerja": "Lengkapi target & realisasi indikator yang belum terukur; "
                          "ukur berkala (triwulanan) dan validasi datanya.",
    "Pelaporan Kinerja": "Susun/lengkapi LKjIP beserta analisis capaian dan analisis "
                         "efisiensi penggunaan anggaran.",
    "Evaluasi Akuntabilitas Kinerja Internal": "Laksanakan evaluasi internal (APIP) dan "
                                               "dokumentasikan tindak lanjut rekomendasi.",
    "Capaian Kinerja": "Tingkatkan realisasi pada indikator bercapaian rendah; analisis "
                       "faktor penghambat dan rencana perbaikannya.",
}


def saran_lanjutan(hasil: HasilEvaluasi) -> list[str]:
    """Saran perbaikan advisory (non-indikator) sesuai gap yang muncul, urut prioritas gap."""
    out: list[str] = []
    seen: set[str] = set()
    for g in hasil.gap:
        if g.komponen in _SARAN_LANJUTAN and g.komponen not in seen:
            seen.add(g.komponen)
            out.append(f"[{g.komponen}] {_SARAN_LANJUTAN[g.komponen]}")
    return out
