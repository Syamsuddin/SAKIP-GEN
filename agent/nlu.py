"""Penerjemah bahasa alami → `Permintaan` yang dapat dieksekusi SAKIP-Gen.

Pengguna boleh menulis kalimat biasa ("tolong nilai kinerja OPD 1 tahun 2026",
"apa kelemahan dinas pendidikan", "draft lkjip opd 1") alih-alih perintah `/slash`.
`parse()` heuristik & deterministik (cepat, gratis, OFFLINE, teruji); `parse_llm()`
fallback berbasis Haiku untuk parafrasa yang tak tertangkap heuristik.

ANTI-HALU: LLM hanya MENERJEMAHKAN niat & MENGEKSTRAK slot — bukan sumber jawaban.
Aksi di luar himpunan AKSI_VALID ditolak. Slot di-grounding ke entitas/nilai nyata.
Aksi DESTRUKTIF (terapkan) TIDAK lewat NL — wajib `/terapkan` + konfirmasi.
"""
from __future__ import annotations

import json
import re

from agent.permintaan import (
    AKSI_VALID,
    Intent,  # alias Permintaan (kompatibilitas)
    Permintaan,
    cari_dokumen,
    cari_level,
    cari_periode,
)

__all__ = ["AKSI_VALID", "Intent", "Permintaan", "parse", "parse_llm", "cocokkan_opd"]


# Urut prioritas: spesifik di atas; "bantuan" PALING AKHIR (fallback generik) agar
# frasa serakah seperti "apa saja" tak membajak permintaan aksi nyata.
_ATURAN: list[tuple[str, list[str]]] = [
    ("daftar_opd", ["daftar opd", "opd apa saja", "ada opd apa", "list opd", "semua opd",
                    "opd yang ada", "opd mana saja", "daftar perangkat daerah"]),
    ("status", ["status saya", "akun saya", "peran saya", "siapa saya", "hak saya", "status akun"]),
    ("benchmark", ["bandingkan", "peringkat", "ranking", "benchmark",
                   "opd lain", "opd terbaik", "dibanding opd"]),
    ("tren", ["tren", "trend", "perkembangan", "dibanding tahun", "tahun lalu",
              "naik turun", "perubahan nilai", "kemajuan"]),
    ("dokumen", ["berkas", "lampiran", "unduh dokumen", "daftar dokumen", "dokumen versi",
                 "file dokumen", "telusur dokumen"]),
    ("laporan", ["lkjip", "lkip", "laporan kinerja", "analisis capaian", "analisis efisiensi",
                 "draft laporan", "narasi capaian", "lhe"]),
    ("temuan", ["temuan", "rekomendasi", "tindak lanjut", "hasil evaluasi", "inspektorat",
                "apip", "evaluasi internal"]),
    ("rencana", ["rencana kinerja", "perencanaan", "renstra", "renja", "rpjmd", "rkpd",
                 "perjanjian kinerja", "pohon kinerja", "cascading", "keselarasan",
                 "sasaran strategis", "sasaran", "indikator utama", "iku"]),
    ("capaian", ["capaian", "realisasi", "target kinerja", "pengukuran", "progres",
                 "tercapai", "berisiko"]),
    ("usulan", ["daftar usulan", "lihat usulan", "riwayat usulan", "usulan yang ada",
                "status usulan"]),
    ("gap", ["gap", "kelemahan", "kekurangan", "celah", "perlu diperbaiki",
             "yang kurang", "prioritas perbaikan"]),
    ("usul", ["usulkan", "buat usulan", "buatkan usulan", "usul ", "perbaiki indikator",
              "rumuskan", "saran perbaikan", "ubah indikator", "jadikan outcome",
              "perbaiki opd", "perbaikan indikator"]),
    ("evaluasi", ["evaluasi", "nilai", "skor", "penilaian", "akip", "kinerja",
                  "bagaimana kinerja", "berapa nilai", "predikat"]),
    ("bantuan", ["bantuan", "help", "bisa apa", "apa saja", "daftar perintah", "fitur", "cara pakai"]),
]

# Aksi yang tak memerlukan referensi OPD (jadi opd_ref tak diekstrak).
_TANPA_OPD = {"status", "bantuan", "benchmark", "daftar_opd"}

_STOPWORD_OPD = {"dinas", "badan", "kantor", "opd", "sekretariat", "inspektorat",
                 "kecamatan", "kelurahan", "perangkat", "daerah", "yang"}


def _tahun(teks: str) -> int | None:
    m = re.search(r"\b(20\d{2})\b", teks)
    return int(m.group(1)) if m else None


def _opd_ref(teks: str) -> str | None:
    """Ambil referensi OPD: 'opd 1', kode kapital (DIKBUD), nama, atau angka polos."""
    s = re.sub(r"\b20\d{2}\b", " ", teks)                      # buang tahun
    m = re.search(r"\bopd\s*[:#]?\s*(\d{1,4})\b", s, re.I)     # "opd 1"
    if m:
        return m.group(1)
    m = re.search(r"\b([A-Z]{3,20})\b", teks)                  # kode kapital, mis. DIKBUD
    if m and m.group(1) != "OPD":                              # 'OPD' bukan kode
        return m.group(1)
    m = re.search(r"\b(?:dinas|badan|kantor|sekretariat|inspektorat|kecamatan|kelurahan)\s+"
                  r"([a-zA-Z][a-zA-Z\s]{2,40})", s, re.I)      # "dinas pendidikan ..."
    if m:
        return f"dinas {m.group(1).strip()}"
    m = re.search(r"\b(\d{1,4})\b", s)                         # angka polos
    if m:
        return m.group(1)
    return None


def parse(teks: str) -> Permintaan | None:
    """Terjemahkan kalimat → Permintaan secara heuristik. None bila tak ada aksi terdeteksi."""
    low = (teks or "").strip().lower()
    if not low:
        return None
    aksi = next((a for a, kws in _ATURAN if any(k in low for k in kws)), None)
    if aksi is None:
        return None
    opd = None if aksi in _TANPA_OPD else _opd_ref(teks)
    return Permintaan(
        aksi=aksi,
        opd_ref=opd,
        tahun=_tahun(low),
        periode=cari_periode(low),
        dokumen=cari_dokumen(low),
        level=cari_level(low),
        skor=1.0,
    )


def cocokkan_opd(ref: str | None, daftar: list[dict]) -> int | None:
    """Petakan referensi OPD (id/kode/nama) ke id, berdasarkan daftar OPD. None bila tak cocok."""
    ref = (ref or "").strip()
    if not ref:
        return None
    if ref.isdigit():
        rid = int(ref)
        return rid if any(int(d["id"]) == rid for d in daftar) else None
    low = ref.lower()
    for d in daftar:                                           # cocokkan kode persis
        if (str(d.get("kode") or "")).lower() == low:
            return int(d["id"])
    kata = [w for w in re.split(r"\s+", low) if len(w) > 2 and w not in _STOPWORD_OPD]
    for d in daftar:                                           # semua kata ada di nama
        nama = (str(d.get("nama") or "")).lower()
        if kata and all(w in nama for w in kata):
            return int(d["id"])
    return None


_SISTEM_NLU = (
    "Anda penerjemah perintah untuk asisten SAKIP pemerintah daerah. Petakan kalimat "
    "pengguna ke SATU aksi dari: rencana, capaian, evaluasi, gap, laporan, temuan, "
    "tren, benchmark, usul, usulan, daftar_opd, dokumen, status, bantuan. "
    "Ekstrak slot bila DISEBUT (selainnya null), JANGAN mengarang: "
    "'opd' (id/kode), 'tahun' (4 digit), 'periode' (tahunan|tw1..tw4|smt1|smt2), "
    "'dokumen' (rpjmd|renstra|renja|rkpd|pk|pohon|lkjip|lhe). "
    'Jawab HANYA JSON satu baris: {"aksi":"...","opd":null,"tahun":null,"periode":null,"dokumen":null}.'
)


async def parse_llm(teks: str, *, settings=None) -> Permintaan | None:
    """Fallback LLM (Haiku) untuk parafrasa yang tak tertangkap heuristik. None bila gagal.

    Anti-halu: keluaran divalidasi keras — aksi wajib ∈ AKSI_VALID; slot di-kanonik-kan;
    nilai tak sah/ngarang diabaikan. LLM tak pernah mengeksekusi.
    """
    from agent.llm import jawab_singkat

    raw = await jawab_singkat(f'Kalimat: "{teks}"', system=_SISTEM_NLU, settings=settings)
    if not raw:
        return None
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except (ValueError, TypeError):
        return None
    aksi = str(d.get("aksi", "")).lower().strip()
    if aksi not in AKSI_VALID:
        return None
    opd = d.get("opd")
    opd = None if opd in (None, "", "null") else str(opd)
    tahun = d.get("tahun")
    tahun = int(tahun) if isinstance(tahun, int) or (isinstance(tahun, str) and tahun.isdigit()) else None
    from agent.permintaan import kanonik_dokumen, kanonik_periode
    return Permintaan(
        aksi=aksi, opd_ref=opd, tahun=tahun,
        periode=kanonik_periode(d.get("periode") if isinstance(d.get("periode"), str) else None),
        dokumen=kanonik_dokumen(d.get("dokumen") if isinstance(d.get("dokumen"), str) else None),
        skor=0.8,
    )
