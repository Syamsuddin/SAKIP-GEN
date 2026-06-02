"""Demo Fase 1 tanpa MySQL: menyemai data contoh ke SQLite, menyusun Dosir
Kinerja, lalu mencetak nilai, predikat, dan gap prioritas.

Jalankan: python demo_evaluasi.py
"""
from __future__ import annotations

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import StaticPool

from agent.service import evaluasi_opd
from db.engines import set_ro_engine

SCHEMA_SQLITE = """
CREATE TABLE opd (id INTEGER PRIMARY KEY, kode TEXT, nama TEXT);
CREATE TABLE sasaran_strategis (id INTEGER PRIMARY KEY, opd_id INTEGER, tahun INTEGER, kode TEXT, uraian TEXT);
CREATE TABLE indikator (id INTEGER PRIMARY KEY, sasaran_id INTEGER, kode TEXT, uraian TEXT, satuan TEXT, tipologi TEXT);
CREATE TABLE capaian_kinerja (id INTEGER PRIMARY KEY, indikator_id INTEGER, opd_id INTEGER, tahun INTEGER, target REAL, realisasi REAL);
CREATE TABLE pelaporan_meta (opd_id INTEGER, tahun INTEGER, ada_lkjip INTEGER, ada_analisis_capaian INTEGER, ada_analisis_efisiensi INTEGER, ada_evaluasi_internal INTEGER, ada_tindak_lanjut INTEGER);
"""

OPD = [{"id": 1, "kode": "DIKBUD", "nama": "Dinas Pendidikan Kabupaten Seruyan"}]
SASARAN = [
    {"id": 1, "opd_id": 1, "tahun": 2026, "kode": "1", "uraian": "Meningkatnya mutu layanan pendidikan dasar"},
    {"id": 2, "opd_id": 1, "tahun": 2026, "kode": "2", "uraian": "Meningkatnya tata kelola pendidikan"},
]
INDIKATOR = [
    {"id": 1, "sasaran_id": 1, "kode": "IKU-1.1", "uraian": "Jumlah sekolah terakreditasi", "satuan": "sekolah", "tipologi": "output"},
    {"id": 2, "sasaran_id": 1, "kode": "IKU-1.2", "uraian": "Persentase sekolah terakreditasi minimal B", "satuan": "persen", "tipologi": "outcome"},
    {"id": 3, "sasaran_id": 2, "kode": "IKU-2.1", "uraian": "Indeks kepuasan layanan pendidikan", "satuan": "indeks", "tipologi": "outcome"},
    {"id": 4, "sasaran_id": 2, "kode": "IKU-2.2", "uraian": "Jumlah dokumen tata kelola disusun", "satuan": "dokumen", "tipologi": "output"},
]
CAPAIAN = [
    {"id": 1, "indikator_id": 1, "opd_id": 1, "tahun": 2026, "target": 120, "realisasi": 96},
    {"id": 2, "indikator_id": 2, "opd_id": 1, "tahun": 2026, "target": 80, "realisasi": 72},
    {"id": 3, "indikator_id": 3, "opd_id": 1, "tahun": 2026, "target": 85, "realisasi": 83},
    # indikator 4 (IKU-2.2) sengaja tanpa capaian -> memunculkan gap pengukuran
]
PELAPORAN = {"opd_id": 1, "tahun": 2026, "ada_lkjip": 1, "ada_analisis_capaian": 1,
             "ada_analisis_efisiensi": 0, "ada_evaluasi_internal": 1, "ada_tindak_lanjut": 0}


async def build_demo_engine() -> AsyncEngine:
    """Buat engine SQLite in-memory, semai skema + data contoh, kembalikan engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        for stmt in filter(str.strip, SCHEMA_SQLITE.split(";")):
            await conn.execute(text(stmt))
        await conn.execute(text("INSERT INTO opd (id,kode,nama) VALUES (:id,:kode,:nama)"), OPD)
        await conn.execute(text("INSERT INTO sasaran_strategis (id,opd_id,tahun,kode,uraian) VALUES (:id,:opd_id,:tahun,:kode,:uraian)"), SASARAN)
        await conn.execute(text("INSERT INTO indikator (id,sasaran_id,kode,uraian,satuan,tipologi) VALUES (:id,:sasaran_id,:kode,:uraian,:satuan,:tipologi)"), INDIKATOR)
        await conn.execute(text("INSERT INTO capaian_kinerja (id,indikator_id,opd_id,tahun,target,realisasi) VALUES (:id,:indikator_id,:opd_id,:tahun,:target,:realisasi)"), CAPAIAN)
        await conn.execute(text("INSERT INTO pelaporan_meta (opd_id,tahun,ada_lkjip,ada_analisis_capaian,ada_analisis_efisiensi,ada_evaluasi_internal,ada_tindak_lanjut) VALUES (:opd_id,:tahun,:ada_lkjip,:ada_analisis_capaian,:ada_analisis_efisiensi,:ada_evaluasi_internal,:ada_tindak_lanjut)"), [PELAPORAN])
    return engine


def cetak(hasil) -> None:
    print("=" * 74)
    print("  ESTIMASI NILAI AKIP (indikatif) — SAKIP-Gen (model heuristik)")
    print("=" * 74)
    print(f"  Instansi : {hasil.instansi}")
    print(f"  Tahun    : {hasil.tahun}\n")
    print(f"  {'Komponen':<46}{'Bobot':>5}{'Skor':>8}{'Kontrib':>12}")
    print("  " + "-" * 72)
    for k in hasil.komponen:
        print(f"  {k.nama:<46}{k.bobot:>5.0f}{k.skor:>8.1f}{k.kontribusi:>12.1f}")
    print("  " + "-" * 72)
    print(f"  {'ESTIMASI NILAI AKIP':<46}{'':>5}{'':>8}{hasil.nilai_total:>12.2f}")
    print(f"\n  Predikat (indikatif) : {hasil.predikat} — {hasil.keterangan_predikat}\n")
    print("  Gap prioritas (urut estimasi kenaikan nilai):")
    for idx, g in enumerate(hasil.gap, 1):
        print(f"   {idx}. [{g.komponen}] {g.deskripsi}  (+{g.estimasi_poin})")
        for d in g.detail:
            print(f"        - {d}")
    if hasil.peringatan:
        print("\n  Peringatan integritas data:")
        for p in hasil.peringatan:
            print(f"   ! {p}")
    print()
    print("  Catatan: estimasi internal (bobot perlu kalibrasi LKE) — bukan Nilai AKIP")
    print("  resmi MenPAN-RB.\n")


async def main() -> None:
    # Demo memakai skema referensi (mainan), apa pun DB_SCHEMA_PROFILE di .env.
    from db.profiles import set_profile
    from db.profiles.reference import ReferenceProfile

    set_profile(ReferenceProfile())
    engine = await build_demo_engine()
    set_ro_engine(engine)
    _, hasil = await evaluasi_opd(opd_id=1, tahun=2026)
    cetak(hasil)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
