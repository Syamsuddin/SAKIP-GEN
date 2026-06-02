"""Tata bahasa terpadu SAKIP-Gen: objek `Permintaan` — satu representasi yang
dihasilkan BAIK oleh parser /slash MAUPUN penerjemah bahasa alami, lalu dieksekusi
oleh satu dispatcher. Lihat docs/USULAN_REFACTOR_PERINTAH.md.

Setiap permintaan = AKSI × OBJEK × LINGKUP × WAKTU, dengan slot bersama:
aksi · opd_ref · tahun · periode · dokumen · level · fokus (+ skor keyakinan).
"""
from __future__ import annotations

from dataclasses import dataclass

# Verba (aksi) yang dikenal. Sengaja tertutup — pondasi anti-halu: apa pun di luar
# himpunan ini ditolak (tak dieksekusi), memicu klarifikasi sopan.
# Nama verba LAMA dipertahankan (kompatibel uji & kebiasaan pengguna); verba BARU
# ditambahkan untuk melengkapi siklus SAKIP.
AKSI_VALID: frozenset[str] = frozenset({
    # lama (sudah berjalan)
    "evaluasi", "gap", "usul", "usulan", "tren", "benchmark",
    "status", "daftar_opd", "bantuan", "terapkan",
    # baru (siklus lengkap)
    "rencana", "capaian", "laporan", "temuan", "dokumen",
})

# Aksi yang BUTUH OPD (selainnya tidak).
AKSI_BUTUH_OPD: frozenset[str] = frozenset({
    "evaluasi", "gap", "usul", "usulan", "tren",
    "rencana", "capaian", "laporan", "temuan", "dokumen",
})

# Aksi DESTRUKTIF — tidak boleh dipicu lewat bahasa alami (wajib /slash + konfirmasi).
AKSI_DESTRUKTIF: frozenset[str] = frozenset({"terapkan"})

PERIODE_VALID: frozenset[str] = frozenset({
    "tahunan", "tw1", "tw2", "tw3", "tw4", "smt1", "smt2",
})
DOKUMEN_VALID: frozenset[str] = frozenset({
    "rpjmd", "renstra", "renja", "rkpd", "pk", "pohon", "lkjip", "lhe",
})
LEVEL_VALID: frozenset[str] = frozenset({"pemda", "opd", "unit", "individu"})

# Sinonim → bentuk kanonik (dipakai parser slash & NLU).
_SINONIM_PERIODE = {
    "triwulan 1": "tw1", "triwulan 2": "tw2", "triwulan 3": "tw3", "triwulan 4": "tw4",
    "tw 1": "tw1", "tw 2": "tw2", "tw 3": "tw3", "tw 4": "tw4",
    "q1": "tw1", "q2": "tw2", "q3": "tw3", "q4": "tw4",
    "semester 1": "smt1", "semester 2": "smt2", "smt 1": "smt1", "smt 2": "smt2",
    "tahunan": "tahunan", "setahun": "tahunan",
}
_SINONIM_DOKUMEN = {
    "rpjmd": "rpjmd", "renstra": "renstra", "renja": "renja", "rkpd": "rkpd",
    "perjanjian kinerja": "pk", "pk": "pk", "pohon kinerja": "pohon", "pohon": "pohon",
    "cascading": "pohon", "keselarasan": "pohon",
    "lkjip": "lkjip", "lkip": "lkjip", "lkj ip": "lkjip",
    "lhe": "lhe", "laporan hasil evaluasi": "lhe",
}
_SINONIM_LEVEL = {
    "pemda": "pemda", "daerah": "pemda", "opd": "opd", "dinas": "opd",
    "unit": "unit", "eselon": "unit", "bidang": "unit", "seksi": "unit",
    "individu": "individu", "pegawai": "individu",
}


@dataclass
class Permintaan:
    aksi: str
    opd_ref: str | None = None          # id / kode / nama / "saya" / "semua"
    tahun: int | None = None
    periode: str | None = None          # tahunan | tw1..tw4 | smt1 | smt2
    dokumen: str | None = None          # rpjmd..lhe
    level: str | None = None            # pemda | opd | unit | individu
    fokus: str | None = None            # teks bebas (nuansa untuk LLM/penyaring)
    skor: float = 1.0                   # keyakinan 0..1 (heuristik=1.0 default; LLM bisa < 1)

    def butuh_opd(self) -> bool:
        return self.aksi in AKSI_BUTUH_OPD


# Alias kompatibilitas: kode/uji lama memakai nama `Intent`.
Intent = Permintaan


def kanonik_periode(teks: str | None) -> str | None:
    if not teks:
        return None
    t = teks.strip().lower()
    if t in PERIODE_VALID:
        return t
    return _SINONIM_PERIODE.get(t)


def kanonik_dokumen(teks: str | None) -> str | None:
    if not teks:
        return None
    t = teks.strip().lower()
    if t in DOKUMEN_VALID:
        return t
    return _SINONIM_DOKUMEN.get(t)


def kanonik_level(teks: str | None) -> str | None:
    if not teks:
        return None
    t = teks.strip().lower()
    if t in LEVEL_VALID:
        return t
    return _SINONIM_LEVEL.get(t)


def cari_periode(teks_low: str) -> str | None:
    """Deteksi periode dari kalimat (frasa lebih panjang diutamakan)."""
    for frasa in sorted(_SINONIM_PERIODE, key=len, reverse=True):
        if frasa in teks_low:
            return _SINONIM_PERIODE[frasa]
    return None


def cari_dokumen(teks_low: str) -> str | None:
    for frasa in sorted(_SINONIM_DOKUMEN, key=len, reverse=True):
        if frasa in teks_low:
            return _SINONIM_DOKUMEN[frasa]
    return None


def cari_level(teks_low: str) -> str | None:
    for frasa in sorted(_SINONIM_LEVEL, key=len, reverse=True):
        if frasa in teks_low:
            return _SINONIM_LEVEL[frasa]
    return None
