"""Profil skema REFERENSI (mainan) — dipakai demo & pengujian.

Skema: opd / sasaran_strategis / indikator / capaian_kinerja / pelaporan_meta
(lihat db/ddl/schema_referensi.sql). Tipologi disimpan langsung pada kolom
`indikator.tipologi`; kolom sumber yang dapat dipromosikan = {uraian, satuan, tipologi}.
"""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from agent.dosir import (
    Capaian,
    DosirKinerja,
    EvaluasiInternal,
    Indikator,
    Meta,
    Pelaporan,
    Pengukuran,
    Perencanaan,
    SasaranStrategis,
)
from db.engines import get_ro_engine

_SQL_OPD = text("SELECT id, kode, nama FROM opd WHERE id = :opd")
_SQL_OPD_BY_KODE = text("SELECT id FROM opd WHERE kode = :kode")
_SQL_DAFTAR_OPD = text("SELECT id, kode, nama FROM opd ORDER BY kode")

_SQL_PERENCANAAN = text(
    """
    SELECT s.kode AS sasaran_kode, s.uraian AS sasaran_uraian,
           i.kode AS indikator_kode, i.uraian AS indikator_uraian,
           i.satuan AS satuan, i.tipologi AS tipologi
    FROM sasaran_strategis s
    JOIN indikator i ON i.sasaran_id = s.id
    WHERE s.opd_id = :opd AND s.tahun = :thn
    ORDER BY s.kode, i.kode
    """
)
_SQL_PENGUKURAN = text(
    """
    SELECT i.kode AS indikator_id, c.target AS target, c.realisasi AS realisasi
    FROM capaian_kinerja c
    JOIN indikator i ON i.id = c.indikator_id
    WHERE c.opd_id = :opd AND c.tahun = :thn
    """
)
_SQL_PELAPORAN = text(
    """
    SELECT ada_lkjip, ada_analisis_capaian, ada_analisis_efisiensi,
           ada_evaluasi_internal, ada_tindak_lanjut
    FROM pelaporan_meta WHERE opd_id = :opd AND tahun = :thn
    """
)

# Sumber indikator untuk promosi (baca + tulis).
_SQL_INDIKATOR = text(
    """
    SELECT i.uraian AS uraian, i.satuan AS satuan, i.tipologi AS tipologi
    FROM indikator i
    JOIN sasaran_strategis s ON s.id = i.sasaran_id
    WHERE i.kode = :kode AND s.opd_id = :opd AND s.tahun = :thn
    """
)
_SQL_LOKASI_INDIKATOR = (
    "SELECT i.id FROM indikator i JOIN sasaran_strategis s ON s.id = i.sasaran_id "
    "WHERE i.kode = :kode AND s.opd_id = :opd AND s.tahun = :thn"
)


def _persen(target, realisasi) -> float | None:
    if target in (None, 0) or realisasi is None:
        return None
    return round(float(realisasi) / float(target) * 100, 2)


def _norm_tipologi(v: str | None) -> str | None:
    return (v or "").lower() or None


class ReferenceProfile:
    name = "reference"
    kolom_diizinkan = frozenset({"uraian", "satuan", "tipologi"})

    async def bangun_dosir(self, opd_id: int, tahun: int) -> DosirKinerja:
        async with get_ro_engine().connect() as c:
            opd = (await c.execute(_SQL_OPD, {"opd": opd_id})).mappings().first()
            ren = (await c.execute(
                _SQL_PERENCANAAN, {"opd": opd_id, "thn": tahun})).mappings().all()
            cap = (await c.execute(
                _SQL_PENGUKURAN, {"opd": opd_id, "thn": tahun})).mappings().all()
            pel = (await c.execute(
                _SQL_PELAPORAN, {"opd": opd_id, "thn": tahun})).mappings().first()

        meta = Meta(instansi=opd["nama"] if opd else f"OPD #{opd_id}",
                    opd_id=opd_id, tahun=tahun, dibuat_pada=datetime.now(UTC))

        sasaran: dict[str, SasaranStrategis] = {}
        for r in ren:
            s = sasaran.get(r["sasaran_kode"])
            if s is None:
                s = SasaranStrategis(kode=r["sasaran_kode"], uraian=r["sasaran_uraian"])
                sasaran[r["sasaran_kode"]] = s
            s.indikator.append(Indikator(
                indikator_id=r["indikator_kode"], uraian=r["indikator_uraian"],
                satuan=r["satuan"], tipologi=_norm_tipologi(r["tipologi"]),
            ))
        perencanaan = Perencanaan(sasaran_strategis=list(sasaran.values()))

        capaian = [
            Capaian(indikator_id=r["indikator_id"], target=r["target"],
                    realisasi=r["realisasi"], persen_capaian=_persen(r["target"], r["realisasi"]))
            for r in cap
        ]
        pengukuran = Pengukuran(capaian=capaian)

        if pel is None:
            pelaporan, evaluasi = Pelaporan(), EvaluasiInternal()
        else:
            pelaporan = Pelaporan(
                ada_lkjip=bool(pel["ada_lkjip"]),
                ada_analisis_capaian=bool(pel["ada_analisis_capaian"]),
                ada_analisis_efisiensi=bool(pel["ada_analisis_efisiensi"]),
            )
            evaluasi = EvaluasiInternal(
                ada_evaluasi_internal=bool(pel["ada_evaluasi_internal"]),
                ada_tindak_lanjut=bool(pel["ada_tindak_lanjut"]),
            )
        return DosirKinerja(meta=meta, perencanaan=perencanaan, pengukuran=pengukuran,
                            pelaporan=pelaporan, evaluasi_internal=evaluasi)

    async def ambil_temuan(self, opd_id: int, tahun: int):
        # Skema referensi (mainan) tak memiliki modul evaluasi internal.
        return []

    async def ambil_capaian(self, opd_id: int, tahun: int, periode: str):
        # Skema referensi tak punya data periodik; capaian disajikan dari bangun_dosir (tahunan).
        return []

    async def ambil_dokumen(self, opd_id: int, tahun: int | None, jenis: str | None):
        # Skema referensi (mainan) tak punya modul manajemen dokumen.
        return []

    async def ambil_cascading(self, opd_id: int, tahun: int):
        # Skema referensi tak punya relasi cascading; keselarasan disajikan heuristik.
        return []

    async def resolve_opd_id(self, ref: str) -> int | None:
        ref = (ref or "").strip()
        if not ref:
            return None
        async with get_ro_engine().connect() as conn:
            if ref.isdigit():
                row = (await conn.execute(_SQL_OPD, {"opd": int(ref)})).mappings().first()
                return int(ref) if row else None
            row = (await conn.execute(_SQL_OPD_BY_KODE, {"kode": ref.upper()})).mappings().first()
        return int(row["id"]) if row else None

    async def daftar_opd(self) -> list[dict]:
        async with get_ro_engine().connect() as conn:
            rows = (await conn.execute(_SQL_DAFTAR_OPD)).mappings().all()
        return [dict(r) for r in rows]

    async def baca_indikator(
        self, conn: AsyncConnection, *, indikator_id: str, opd_id: int, tahun: int
    ) -> Indikator | None:
        row = (await conn.execute(
            _SQL_INDIKATOR, {"kode": indikator_id, "opd": opd_id, "thn": tahun}
        )).mappings().first()
        if row is None:
            return None
        return Indikator(indikator_id=indikator_id, uraian=row["uraian"],
                         satuan=row["satuan"], tipologi=_norm_tipologi(row["tipologi"]))

    async def terapkan_indikator(
        self, conn: AsyncConnection, *, indikator_id: str, opd_id: int, tahun: int,
        nilai: dict[str, str | None],
    ) -> None:
        # Kunci `nilai` dijamin subset kolom_diizinkan (= nama kolom fisik di profil ini).
        set_clause = ", ".join(f"{k} = :{k}" for k in nilai)
        sql = text(
            f"UPDATE indikator SET {set_clause} WHERE id IN ({_SQL_LOKASI_INDIKATOR})"
        )
        await conn.execute(sql, {**nilai, "kode": indikator_id, "opd": opd_id, "thn": tahun})
