"""Profil skema eSAKIP nyata (default produksi) — lihat db/mysql/schema.sql.

Pemetaan ke model Dosir:
- OPD          ← unit_organisasi (level_unit='OPD')
- Sasaran      ← sakip_kinerja_node (jenis_node SASARAN_OPD/TUJUAN_OPD, level OPD)
- Indikator    ← sakip_indikator (indikator_id = sakip_indikator.id; tipologi = jenis_indikator)
- Capaian      ← sakip_target + sakip_realisasi (periode TAHUNAN)
- Pelaporan    ← lkjip_dokumen + lkjip_capaian (narasi analisis/efisiensi)
- Eval internal← evaluasi_akip/evaluasi_unit + rantai tindak lanjut

Promosi: field Dosir {uraian→nama, tipologi→jenis_indikator}. `satuan` (FK ref_satuan)
belum dipromosikan (butuh resolusi referensi); jadi kolom_diizinkan = {uraian, tipologi}.
Identitas indikator memakai PK `sakip_indikator.id` (stabil), bukan kode opsional.
"""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from agent.dokumen import Dokumen
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
from agent.evaluasi import Rekomendasi, Temuan
from agent.keselarasan import RelasiKinerja
from db.engines import get_ro_engine

# Skema minimal kompatibel-SQLite untuk pengujian profil ini (subset kolom yang dipakai).
SCHEMA_SQLITE_MINI = """
CREATE TABLE unit_organisasi (id INTEGER PRIMARY KEY, kode_unit TEXT, nama TEXT, level_unit TEXT);
CREATE TABLE ref_satuan (id INTEGER PRIMARY KEY, kode TEXT, nama TEXT);
CREATE TABLE sakip_kinerja_node (id INTEGER PRIMARY KEY, unit_id INTEGER, kode TEXT, uraian TEXT, jenis_node TEXT, status TEXT, tahun_awal INTEGER, tahun_akhir INTEGER);
CREATE TABLE sakip_indikator (id INTEGER PRIMARY KEY, node_id INTEGER, kode TEXT, nama TEXT, satuan_id INTEGER, jenis_indikator TEXT, status TEXT);
CREATE TABLE sakip_target (id INTEGER PRIMARY KEY, indikator_id INTEGER, tahun INTEGER, periode TEXT, target_angka REAL);
CREATE TABLE sakip_realisasi (id INTEGER PRIMARY KEY, indikator_id INTEGER, tahun INTEGER, periode TEXT, realisasi_angka REAL);
CREATE TABLE lkjip_dokumen (id INTEGER PRIMARY KEY, unit_id INTEGER, tahun INTEGER);
CREATE TABLE lkjip_capaian (id INTEGER PRIMARY KEY, lkjip_id INTEGER, narasi_analisis TEXT, narasi_efisiensi TEXT);
CREATE TABLE evaluasi_akip (id INTEGER PRIMARY KEY, tahun INTEGER, jenis_evaluasi TEXT);
CREATE TABLE evaluasi_unit (id INTEGER PRIMARY KEY, evaluasi_id INTEGER, unit_id INTEGER);
CREATE TABLE evaluasi_temuan (id INTEGER PRIMARY KEY, evaluasi_unit_id INTEGER, jenis_temuan TEXT, uraian TEXT, tingkat_risiko TEXT);
CREATE TABLE evaluasi_rekomendasi (id INTEGER PRIMARY KEY, temuan_id INTEGER, rekomendasi TEXT, prioritas TEXT, status TEXT);
CREATE TABLE evaluasi_tindak_lanjut (id INTEGER PRIMARY KEY, rekomendasi_id INTEGER, uraian_tindak_lanjut TEXT, progres_persen REAL, status TEXT);
CREATE TABLE ref_dokumen_jenis (id INTEGER PRIMARY KEY, kode TEXT, nama TEXT, kelompok TEXT, level_dokumen TEXT);
CREATE TABLE dokumen (id INTEGER PRIMARY KEY, pemda_id INTEGER, unit_id INTEGER, jenis_dokumen_id INTEGER, tahun INTEGER, nomor_dokumen TEXT, judul TEXT, status TEXT, tanggal_penetapan TEXT);
CREATE TABLE dokumen_versi (id INTEGER PRIMARY KEY, dokumen_id INTEGER, versi INTEGER, nama_file TEXT);
CREATE TABLE dokumen_bukti (id INTEGER PRIMARY KEY, dokumen_id INTEGER, pemda_id INTEGER, unit_id INTEGER, tahun INTEGER, judul TEXT);
CREATE TABLE sakip_cascading_relasi (id INTEGER PRIMARY KEY, parent_node_id INTEGER, child_node_id INTEGER, jenis_relasi TEXT, bobot_kontribusi REAL);
"""

_SQL_OPD = text("SELECT id, kode_unit AS kode, nama FROM unit_organisasi WHERE id = :opd")
_SQL_OPD_BY_KODE = text("SELECT id FROM unit_organisasi WHERE kode_unit = :kode")
_SQL_DAFTAR_OPD = text(
    "SELECT id, kode_unit AS kode, nama FROM unit_organisasi "
    "WHERE level_unit = 'OPD' ORDER BY kode_unit"
)

_SQL_PERENCANAAN = text(
    """
    SELECT COALESCE(n.kode, CAST(n.id AS CHAR)) AS sasaran_kode, n.uraian AS sasaran_uraian,
           i.id AS indikator_id, i.nama AS indikator_uraian,
           sat.kode AS satuan, i.jenis_indikator AS tipologi
    FROM sakip_kinerja_node n
    JOIN sakip_indikator i ON i.node_id = n.id
    LEFT JOIN ref_satuan sat ON sat.id = i.satuan_id
    WHERE n.unit_id = :opd
      AND n.jenis_node IN ('SASARAN_OPD', 'TUJUAN_OPD')
      AND n.status = 'AKTIF'
      AND :thn BETWEEN n.tahun_awal AND n.tahun_akhir
    ORDER BY n.kode, i.kode
    """
)
_SQL_PENGUKURAN = text(
    """
    SELECT i.id AS indikator_id, t.target_angka AS target, r.realisasi_angka AS realisasi
    FROM sakip_indikator i
    JOIN sakip_kinerja_node n ON n.id = i.node_id
    LEFT JOIN sakip_target t
      ON t.indikator_id = i.id AND t.tahun = :thn AND t.periode = 'TAHUNAN'
    LEFT JOIN sakip_realisasi r
      ON r.indikator_id = i.id AND r.tahun = :thn AND r.periode = 'TAHUNAN'
    WHERE n.unit_id = :opd AND n.status = 'AKTIF'
      AND :thn BETWEEN n.tahun_awal AND n.tahun_akhir
    """
)

_SQL_ADA_LKJIP = text(
    "SELECT EXISTS(SELECT 1 FROM lkjip_dokumen WHERE unit_id = :opd AND tahun = :thn) AS ada"
)
_SQL_ADA_ANALISIS = text(
    """
    SELECT EXISTS(
      SELECT 1 FROM lkjip_capaian lc JOIN lkjip_dokumen ld ON ld.id = lc.lkjip_id
      WHERE ld.unit_id = :opd AND ld.tahun = :thn
        AND lc.narasi_analisis IS NOT NULL AND lc.narasi_analisis <> ''
    ) AS ada
    """
)
_SQL_ADA_EFISIENSI = text(
    """
    SELECT EXISTS(
      SELECT 1 FROM lkjip_capaian lc JOIN lkjip_dokumen ld ON ld.id = lc.lkjip_id
      WHERE ld.unit_id = :opd AND ld.tahun = :thn
        AND lc.narasi_efisiensi IS NOT NULL AND lc.narasi_efisiensi <> ''
    ) AS ada
    """
)
_SQL_ADA_EVALUASI = text(
    """
    SELECT EXISTS(
      SELECT 1 FROM evaluasi_unit eu JOIN evaluasi_akip ea ON ea.id = eu.evaluasi_id
      WHERE eu.unit_id = :opd AND ea.tahun = :thn
        AND ea.jenis_evaluasi IN ('MANDIRI', 'INTERNAL_INSPEKTORAT', 'REVIU')
    ) AS ada
    """
)
_SQL_ADA_TINDAK_LANJUT = text(
    """
    SELECT EXISTS(
      SELECT 1 FROM evaluasi_tindak_lanjut tl
      JOIN evaluasi_rekomendasi rk ON rk.id = tl.rekomendasi_id
      JOIN evaluasi_temuan tm ON tm.id = rk.temuan_id
      JOIN evaluasi_unit eu ON eu.id = tm.evaluasi_unit_id
      JOIN evaluasi_akip ea ON ea.id = eu.evaluasi_id
      WHERE eu.unit_id = :opd AND ea.tahun = :thn
    ) AS ada
    """
)

_SQL_INDIKATOR = text(
    """
    SELECT i.nama AS uraian, sat.kode AS satuan, i.jenis_indikator AS tipologi
    FROM sakip_indikator i LEFT JOIN ref_satuan sat ON sat.id = i.satuan_id
    WHERE i.id = :id
    """
)

# field Dosir -> kolom fisik sakip_indikator
_KOLOM_FISIK = {"uraian": "nama", "tipologi": "jenis_indikator"}

# periode kanonik (Permintaan) -> nilai ENUM di sakip_target/sakip_realisasi
_PERIODE_DB = {
    "tahunan": "TAHUNAN", "tw1": "TRIWULAN_1", "tw2": "TRIWULAN_2",
    "tw3": "TRIWULAN_3", "tw4": "TRIWULAN_4", "smt1": "SEMESTER_1", "smt2": "SEMESTER_2",
}

_SQL_CAPAIAN_PERIODE = text(
    """
    SELECT i.id AS indikator_id, t.target_angka AS target, r.realisasi_angka AS realisasi
    FROM sakip_indikator i
    JOIN sakip_kinerja_node n ON n.id = i.node_id
    LEFT JOIN sakip_target t
      ON t.indikator_id = i.id AND t.tahun = :thn AND t.periode = :per
    LEFT JOIN sakip_realisasi r
      ON r.indikator_id = i.id AND r.tahun = :thn AND r.periode = :per
    WHERE n.unit_id = :opd AND n.status = 'AKTIF'
      AND :thn BETWEEN n.tahun_awal AND n.tahun_akhir
    """
)

# dokumen kanonik (Permintaan) -> kode ref_dokumen_jenis (level OPD). `pohon` bukan dokumen.
_DOK_KODE = {
    "rpjmd": "RPJMD", "rkpd": "RKPD", "renstra": "RENSTRA", "renja": "RENJA",
    "pk": "PK", "lkjip": "LKJIP_OPD", "lhe": "LHE",
}

_SQL_DOKUMEN = text(
    """
    SELECT j.kode AS jenis, j.nama AS nama_jenis, d.judul AS judul, d.status AS status,
           d.tahun AS tahun, d.nomor_dokumen AS nomor,
           (SELECT COUNT(*) FROM dokumen_versi v WHERE v.dokumen_id = d.id) AS jumlah_versi,
           (SELECT MAX(v.versi) FROM dokumen_versi v WHERE v.dokumen_id = d.id) AS versi_terakhir,
           (SELECT COUNT(*) FROM dokumen_bukti b WHERE b.dokumen_id = d.id) AS jumlah_bukti
    FROM dokumen d
    JOIN ref_dokumen_jenis j ON j.id = d.jenis_dokumen_id
    WHERE d.unit_id = :opd
      AND (:thn IS NULL OR d.tahun IS NULL OR d.tahun = :thn)
      AND (:kode IS NULL OR j.kode = :kode)
    ORDER BY d.tahun DESC, j.kode
    """
)

# Relasi cascading yang melibatkan node milik OPD (sebagai anak ATAU induk).
_SQL_CASCADING = text(
    """
    SELECT pr.uraian AS parent_uraian, ch.uraian AS child_uraian,
           c.jenis_relasi AS jenis, c.bobot_kontribusi AS bobot,
           pr.unit_id AS parent_unit, ch.unit_id AS child_unit
    FROM sakip_cascading_relasi c
    JOIN sakip_kinerja_node pr ON pr.id = c.parent_node_id
    JOIN sakip_kinerja_node ch ON ch.id = c.child_node_id
    WHERE (pr.unit_id = :opd OR ch.unit_id = :opd)
      AND pr.status = 'AKTIF' AND ch.status = 'AKTIF'
      AND :thn BETWEEN ch.tahun_awal AND ch.tahun_akhir
    ORDER BY c.id
    """
)

_SQL_TEMUAN = text(
    """
    SELECT t.id AS temuan_id, t.uraian AS temuan, t.jenis_temuan AS jenis,
           t.tingkat_risiko AS risiko,
           r.id AS rek_id, r.rekomendasi AS rekomendasi, r.prioritas AS prioritas,
           r.status AS rek_status,
           tl.progres_persen AS progres, tl.status AS tl_status
    FROM evaluasi_temuan t
    JOIN evaluasi_unit eu ON eu.id = t.evaluasi_unit_id
    JOIN evaluasi_akip ea ON ea.id = eu.evaluasi_id
    LEFT JOIN evaluasi_rekomendasi r ON r.temuan_id = t.id
    LEFT JOIN evaluasi_tindak_lanjut tl ON tl.rekomendasi_id = r.id
    WHERE eu.unit_id = :opd AND ea.tahun = :thn
    ORDER BY t.id, r.id, tl.id
    """
)


def _persen(target, realisasi) -> float | None:
    if target in (None, 0) or realisasi is None:
        return None
    return round(float(realisasi) / float(target) * 100, 2)


def _tipologi(v: str | None) -> str | None:
    return (v or "").lower() or None


class EsakipProfile:
    name = "esakip"
    kolom_diizinkan = frozenset({"uraian", "tipologi"})

    async def bangun_dosir(self, opd_id: int, tahun: int) -> DosirKinerja:
        p = {"opd": opd_id, "thn": tahun}
        async with get_ro_engine().connect() as c:
            opd = (await c.execute(_SQL_OPD, {"opd": opd_id})).mappings().first()
            ren = (await c.execute(_SQL_PERENCANAAN, p)).mappings().all()
            cap = (await c.execute(_SQL_PENGUKURAN, p)).mappings().all()
            ada_lkjip = (await c.execute(_SQL_ADA_LKJIP, p)).scalar()
            ada_anls = (await c.execute(_SQL_ADA_ANALISIS, p)).scalar()
            ada_efis = (await c.execute(_SQL_ADA_EFISIENSI, p)).scalar()
            ada_eval = (await c.execute(_SQL_ADA_EVALUASI, p)).scalar()
            ada_tl = (await c.execute(_SQL_ADA_TINDAK_LANJUT, p)).scalar()

        meta = Meta(instansi=opd["nama"] if opd else f"OPD #{opd_id}",
                    opd_id=opd_id, tahun=tahun, dibuat_pada=datetime.now(UTC))

        sasaran: dict[str, SasaranStrategis] = {}
        for r in ren:
            s = sasaran.get(r["sasaran_kode"])
            if s is None:
                s = SasaranStrategis(kode=r["sasaran_kode"], uraian=r["sasaran_uraian"])
                sasaran[r["sasaran_kode"]] = s
            s.indikator.append(Indikator(
                indikator_id=str(r["indikator_id"]), uraian=r["indikator_uraian"],
                satuan=r["satuan"], tipologi=_tipologi(r["tipologi"]),
            ))
        perencanaan = Perencanaan(sasaran_strategis=list(sasaran.values()))

        capaian = [
            Capaian(indikator_id=str(r["indikator_id"]), target=r["target"],
                    realisasi=r["realisasi"], persen_capaian=_persen(r["target"], r["realisasi"]))
            for r in cap
        ]
        pengukuran = Pengukuran(capaian=capaian)

        pelaporan = Pelaporan(
            ada_lkjip=bool(ada_lkjip),
            ada_analisis_capaian=bool(ada_anls),
            ada_analisis_efisiensi=bool(ada_efis),
        )
        evaluasi = EvaluasiInternal(
            ada_evaluasi_internal=bool(ada_eval), ada_tindak_lanjut=bool(ada_tl)
        )
        return DosirKinerja(meta=meta, perencanaan=perencanaan, pengukuran=pengukuran,
                            pelaporan=pelaporan, evaluasi_internal=evaluasi)

    async def resolve_opd_id(self, ref: str) -> int | None:
        ref = (ref or "").strip()
        if not ref:
            return None
        async with get_ro_engine().connect() as conn:
            if ref.isdigit():
                row = (await conn.execute(_SQL_OPD, {"opd": int(ref)})).mappings().first()
                return int(ref) if row else None
            row = (await conn.execute(_SQL_OPD_BY_KODE, {"kode": ref})).mappings().first()
        return int(row["id"]) if row else None

    async def daftar_opd(self) -> list[dict]:
        async with get_ro_engine().connect() as conn:
            rows = (await conn.execute(_SQL_DAFTAR_OPD)).mappings().all()
        return [dict(r) for r in rows]

    async def ambil_capaian(self, opd_id: int, tahun: int, periode: str) -> list[Capaian]:
        per_db = _PERIODE_DB.get(periode, "TAHUNAN")
        async with get_ro_engine().connect() as conn:
            rows = (await conn.execute(
                _SQL_CAPAIAN_PERIODE, {"opd": opd_id, "thn": tahun, "per": per_db}
            )).mappings().all()
        return [
            Capaian(indikator_id=str(r["indikator_id"]), target=r["target"],
                    realisasi=r["realisasi"], persen_capaian=_persen(r["target"], r["realisasi"]))
            for r in rows
            if r["target"] is not None or r["realisasi"] is not None  # hanya yang punya data periode itu
        ]

    async def ambil_dokumen(
        self, opd_id: int, tahun: int | None, jenis: str | None
    ) -> list[Dokumen]:
        # `pohon` (cascading) bukan dokumen → kembalikan kosong (pakai /rencana dok=pohon).
        if jenis == "pohon":
            return []
        kode = _DOK_KODE.get(jenis) if jenis else None
        async with get_ro_engine().connect() as conn:
            rows = (await conn.execute(
                _SQL_DOKUMEN, {"opd": opd_id, "thn": tahun, "kode": kode}
            )).mappings().all()
        return [
            Dokumen(
                jenis=r["jenis"], nama_jenis=r["nama_jenis"], judul=r["judul"],
                status=r["status"], tahun=r["tahun"], nomor=r["nomor"],
                jumlah_versi=int(r["jumlah_versi"] or 0),
                versi_terakhir=r["versi_terakhir"],
                jumlah_bukti=int(r["jumlah_bukti"] or 0),
            )
            for r in rows
        ]

    async def ambil_cascading(self, opd_id: int, tahun: int) -> list[RelasiKinerja]:
        async with get_ro_engine().connect() as conn:
            rows = (await conn.execute(
                _SQL_CASCADING, {"opd": opd_id, "thn": tahun})).mappings().all()
        hasil: list[RelasiKinerja] = []
        for r in rows:
            # arah relatif OPD: node OPD sebagai ANAK → "naik" (kontribusi ke atasan);
            # node OPD sebagai INDUK → "turun" (cascade ke unit/eselon).
            arah = "naik" if r["child_unit"] == opd_id else "turun"
            hasil.append(RelasiKinerja(
                parent=r["parent_uraian"], child=r["child_uraian"],
                jenis=r["jenis"], bobot=r["bobot"], arah=arah,
            ))
        return hasil

    async def ambil_temuan(self, opd_id: int, tahun: int) -> list[Temuan]:
        async with get_ro_engine().connect() as conn:
            rows = (await conn.execute(_SQL_TEMUAN, {"opd": opd_id, "thn": tahun})).mappings().all()
        temuan_map: dict[int, Temuan] = {}
        rek_map: dict[int, Rekomendasi] = {}
        for r in rows:
            t = temuan_map.get(r["temuan_id"])
            if t is None:
                t = Temuan(uraian=r["temuan"] or "", jenis=r["jenis"],
                           tingkat_risiko=r["risiko"])
                temuan_map[r["temuan_id"]] = t
            rid = r["rek_id"]
            if rid is None:
                continue
            rek = rek_map.get(rid)
            if rek is None:
                rek = Rekomendasi(uraian=r["rekomendasi"] or "", prioritas=r["prioritas"],
                                  status=r["rek_status"], tindak_lanjut=r["tl_status"],
                                  progres=r["progres"])
                rek_map[rid] = rek
                t.rekomendasi.append(rek)
            elif r["progres"] is not None and (rek.progres is None or r["progres"] > rek.progres):
                rek.progres = r["progres"]           # ambil tindak lanjut dengan progres tertinggi
                rek.tindak_lanjut = r["tl_status"]
        return list(temuan_map.values())

    async def baca_indikator(
        self, conn: AsyncConnection, *, indikator_id: str, opd_id: int, tahun: int
    ) -> Indikator | None:
        if not str(indikator_id).isdigit():
            return None
        row = (await conn.execute(
            _SQL_INDIKATOR, {"id": int(indikator_id)})).mappings().first()
        if row is None:
            return None
        return Indikator(indikator_id=indikator_id, uraian=row["uraian"],
                         satuan=row["satuan"], tipologi=_tipologi(row["tipologi"]))

    async def terapkan_indikator(
        self, conn: AsyncConnection, *, indikator_id: str, opd_id: int, tahun: int,
        nilai: dict[str, str | None],
    ) -> None:
        set_parts: list[str] = []
        params: dict[str, object] = {"id": int(indikator_id)}
        for field, val in nilai.items():
            kolom = _KOLOM_FISIK[field]            # kunci sudah lolos kolom_diizinkan
            if field == "tipologi" and val is not None:
                val = val.upper()                  # jenis_indikator = ENUM huruf besar
            set_parts.append(f"{kolom} = :{field}")
            params[field] = val
        sql = text(f"UPDATE sakip_indikator SET {', '.join(set_parts)} WHERE id = :id")
        await conn.execute(sql, params)
