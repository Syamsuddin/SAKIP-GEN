"""Model telusur dokumen SAKIP: berkas + versi + bukti dukung.

Dibaca read-only dari skema sumber lewat profil (db/profiles/*.ambil_dokumen).
Memetakan tabel `dokumen` + `dokumen_versi` + `dokumen_bukti` (lihat db/mysql/schema.sql)
ke ringkasan ramah-bot. Agen TIDAK menyusun dokumen resmi — hanya menelusur keberadaan,
versi terakhir, dan jumlah bukti sebagai penanda kelengkapan SAKIP.
"""
from __future__ import annotations

from pydantic import BaseModel


class Dokumen(BaseModel):
    jenis: str                           # kode jenis (RPJMD/RENSTRA/PK/LKJIP_OPD/…)
    nama_jenis: str                      # nama panjang jenis dokumen
    judul: str
    status: str | None = None            # DRAFT/DITETAPKAN/… (status dokumen)
    tahun: int | None = None
    nomor: str | None = None             # nomor dokumen (bila ada)
    jumlah_versi: int = 0
    versi_terakhir: int | None = None
    jumlah_bukti: int = 0
