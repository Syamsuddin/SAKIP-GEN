"""Kontrak profil skema sumber — lapisan adaptasi agar SAKIP-Gen jalan di eSAKIP manapun.

Logika agen hanya mengenal model domain (DosirKinerja/Indikator). Setiap profil
menerjemahkan skema fisik suatu aplikasi SAKIP ke/dari model itu:

- BACA   : `bangun_dosir`, `resolve_opd_id`, `daftar_opd` (jalur read-only RO).
- TULIS  : `baca_indikator` + `terapkan_indikator` (dipanggil dalam transaksi promotor;
           menerima `conn` agar satu transaksi dengan audit & penanda status).
- `kolom_diizinkan` : nama-FIELD Dosir yang boleh dipromosikan profil ini
  (mis. {"uraian","satuan","tipologi"}). Mapping ke kolom fisik ditangani profil.

Onboarding eSAKIP baru = menulis satu kelas profil; tidak menyentuh kode inti.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncConnection

from agent.dokumen import Dokumen
from agent.dosir import Capaian, DosirKinerja, Indikator
from agent.evaluasi import Temuan
from agent.keselarasan import RelasiKinerja


@runtime_checkable
class SchemaProfile(Protocol):
    name: str
    kolom_diizinkan: frozenset[str]

    # --- BACA ---
    async def bangun_dosir(self, opd_id: int, tahun: int) -> DosirKinerja: ...
    async def resolve_opd_id(self, ref: str) -> int | None: ...
    async def daftar_opd(self) -> list[dict]: ...

    async def ambil_temuan(self, opd_id: int, tahun: int) -> list[Temuan]:
        """Temuan evaluasi internal + rekomendasi + status tindak lanjut. [] bila tak ada/tak didukung."""
        ...

    async def ambil_capaian(self, opd_id: int, tahun: int, periode: str) -> list[Capaian]:
        """Capaian per PERIODE (tahunan|tw1..tw4|smt1|smt2). [] bila periode tak punya data/tak didukung."""
        ...

    async def ambil_dokumen(
        self, opd_id: int, tahun: int | None, jenis: str | None
    ) -> list[Dokumen]:
        """Telusur dokumen OPD (+ versi & bukti). `jenis` kanonik (rpjmd..lhe) atau None=semua.
        [] bila tak ada/tak didukung."""
        ...

    async def ambil_cascading(self, opd_id: int, tahun: int) -> list[RelasiKinerja]:
        """Relasi cascading/keselarasan pohon kinerja yang melibatkan node OPD.
        [] bila tak ada/tak didukung."""
        ...

    # --- TULIS (sumber), dalam transaksi promotor ---
    async def baca_indikator(
        self, conn: AsyncConnection, *, indikator_id: str, opd_id: int, tahun: int
    ) -> Indikator | None:
        """Kondisi sumber indikator saat ini sebagai objek Dosir (untuk hash & audit)."""
        ...

    async def terapkan_indikator(
        self, conn: AsyncConnection, *, indikator_id: str, opd_id: int, tahun: int,
        nilai: dict[str, str | None],
    ) -> None:
        """UPDATE kolom sumber dari {field_Dosir: nilai}. Kunci `nilai` sudah lolos whitelist."""
        ...
