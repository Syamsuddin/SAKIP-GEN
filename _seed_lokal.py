"""Siapkan local_esakip.db (SQLite, skema eSAKIP + tabel agen) untuk uji bot live.
Jalankan: .venv/bin/python _seed_lokal.py  (file dipakai dev_polling via DB_*_URL)."""
from __future__ import annotations

import asyncio
import os

from sqlalchemy import text as sqltext
from sqlalchemy.ext.asyncio import create_async_engine

from db.profiles.esakip import SCHEMA_SQLITE_MINI
from db.schema import buat_skema_agen

SEED = [
    "INSERT INTO unit_organisasi (id,kode_unit,nama,level_unit) VALUES "
    "(1,'DIKBUD','Dinas Pendidikan Kabupaten Seruyan','OPD'),"
    "(2,'DINKES','Dinas Kesehatan Kabupaten Seruyan','OPD')",
    "INSERT INTO ref_satuan (id,kode,nama) VALUES (1,'unit','Unit'),(2,'persen','Persen'),(3,'indeks','Indeks')",
    "INSERT INTO sakip_kinerja_node (id,unit_id,kode,uraian,jenis_node,status,tahun_awal,tahun_akhir) VALUES "
    "(1,1,'1','Meningkatnya mutu layanan pendidikan dasar','SASARAN_OPD','AKTIF',2024,2027),"
    "(2,1,'2','Meningkatnya tata kelola pendidikan','SASARAN_OPD','AKTIF',2024,2027),"
    "(3,2,'1','Meningkatnya derajat kesehatan masyarakat','SASARAN_OPD','AKTIF',2024,2027),"
    "(100,99,'P1','Meningkatnya kualitas SDM yang berdaya saing','SASARAN_PEMDA','AKTIF',2024,2027),"
    "(200,201,'1.1','Terlaksananya akreditasi sekolah','SASARAN_UNIT','AKTIF',2024,2027)",
    # Cascading DIKBUD(1): kontribusi ke Pemda(100) [naik] & diturunkan ke unit(200) [turun]
    "INSERT INTO sakip_cascading_relasi (id,parent_node_id,child_node_id,jenis_relasi,bobot_kontribusi) VALUES "
    "(1,100,1,'KONTRIBUSI',60),(2,1,200,'TURUNAN_LANGSUNG',NULL)",
    "INSERT INTO sakip_indikator (id,node_id,kode,nama,satuan_id,jenis_indikator,status) VALUES "
    "(11,1,'IKU-1.1','Jumlah sekolah terakreditasi',1,'OUTPUT','AKTIF'),"
    "(12,1,'IKU-1.2','Persentase sekolah terakreditasi minimal B',2,'OUTCOME','AKTIF'),"
    "(13,2,'IKU-2.1','Indeks kepuasan layanan pendidikan',3,'OUTCOME','AKTIF'),"
    "(14,2,'IKU-2.2','Jumlah dokumen tata kelola disusun',1,'OUTPUT','AKTIF'),"
    "(21,3,'IKK-3.1','Persentase desa UCI imunisasi',2,'OUTCOME','AKTIF')",
    "INSERT INTO sakip_target (id,indikator_id,tahun,periode,target_angka) VALUES "
    "(1,11,2026,'TAHUNAN',120),(2,12,2026,'TAHUNAN',80),(3,13,2026,'TAHUNAN',85),(4,21,2026,'TAHUNAN',90),"
    "(5,11,2025,'TAHUNAN',120),(6,12,2025,'TAHUNAN',80),(7,13,2025,'TAHUNAN',85),"
    # Capaian triwulanan 2026 (DIKBUD: 11,12,13) untuk demo /capaian tw1..tw2
    "(11,11,2026,'TRIWULAN_1',30),(12,12,2026,'TRIWULAN_1',20),(13,13,2026,'TRIWULAN_1',85),"
    "(14,11,2026,'TRIWULAN_2',60),(15,12,2026,'TRIWULAN_2',40),(16,13,2026,'TRIWULAN_2',85)",
    "INSERT INTO sakip_realisasi (id,indikator_id,tahun,periode,realisasi_angka) VALUES "
    "(1,11,2026,'TAHUNAN',96),(2,12,2026,'TAHUNAN',72),(3,13,2026,'TAHUNAN',83),(4,21,2026,'TAHUNAN',58),"
    "(5,11,2025,'TAHUNAN',60),(6,12,2025,'TAHUNAN',55),(7,13,2025,'TAHUNAN',70),"
    "(11,11,2026,'TRIWULAN_1',24),(12,12,2026,'TRIWULAN_1',19),(13,13,2026,'TRIWULAN_1',80),"
    "(14,11,2026,'TRIWULAN_2',55),(15,12,2026,'TRIWULAN_2',38),(16,13,2026,'TRIWULAN_2',82)",
    "INSERT INTO lkjip_dokumen (id,unit_id,tahun) VALUES (1,1,2026)",
    "INSERT INTO lkjip_capaian (id,lkjip_id,narasi_analisis,narasi_efisiensi) VALUES (1,1,'Analisis capaian ada',NULL)",
    "INSERT INTO evaluasi_akip (id,tahun,jenis_evaluasi) VALUES (1,2026,'INTERNAL_INSPEKTORAT')",
    "INSERT INTO evaluasi_unit (id,evaluasi_id,unit_id) VALUES (1,1,1)",
    "INSERT INTO evaluasi_temuan (id,evaluasi_unit_id,jenis_temuan,uraian,tingkat_risiko) VALUES "
    "(1,1,'KELEMAHAN','Sebagian indikator belum berorientasi hasil (outcome)','SEDANG'),"
    "(2,1,'KETIDAKSESUAIAN','Analisis efisiensi anggaran belum ada di LKjIP','RENDAH')",
    "INSERT INTO evaluasi_rekomendasi (id,temuan_id,rekomendasi,prioritas,status) VALUES "
    "(1,1,'Rumuskan ulang IKU output menjadi outcome','TINGGI','DITINDAKLANJUTI'),"
    "(2,2,'Tambahkan analisis efisiensi anggaran pada LKjIP','SEDANG','BARU')",
    "INSERT INTO evaluasi_tindak_lanjut (id,rekomendasi_id,uraian_tindak_lanjut,progres_persen,status) VALUES "
    "(1,1,'Draft IKU outcome telah disusun & direviu',60,'DIAJUKAN')",
    # Dokumen SAKIP (DIKBUD: Renstra+PK+LKjIP; DINKES: Renstra)
    "INSERT INTO ref_dokumen_jenis (id,kode,nama,kelompok,level_dokumen) VALUES "
    "(1,'RENSTRA','Rencana Strategis Perangkat Daerah','PERENCANAAN','OPD'),"
    "(2,'PK','Perjanjian Kinerja','PENGUKURAN','OPD'),"
    "(3,'LKJIP_OPD','Laporan Kinerja Perangkat Daerah','PELAPORAN','OPD')",
    "INSERT INTO dokumen (id,pemda_id,unit_id,jenis_dokumen_id,tahun,nomor_dokumen,judul,status) VALUES "
    "(1,1,1,1,2024,'050/123','Renstra Dinas Pendidikan 2024-2027','DITETAPKAN'),"
    "(2,1,1,2,2026,'PK/DIKBUD/2026','Perjanjian Kinerja Dinas Pendidikan 2026','DITETAPKAN'),"
    "(3,1,1,3,2025,'LKJIP/DIKBUD/2025','LKjIP Dinas Pendidikan 2025','DITETAPKAN'),"
    "(4,1,2,1,2024,'440/77','Renstra Dinas Kesehatan 2024-2027','DITETAPKAN')",
    "INSERT INTO dokumen_versi (id,dokumen_id,versi,nama_file) VALUES "
    "(1,1,1,'renstra_dikbud_v1.pdf'),(2,1,2,'renstra_dikbud_v2.pdf'),"
    "(3,2,1,'pk_dikbud_2026.pdf'),(4,3,1,'lkjip_dikbud_2025.pdf'),(5,4,1,'renstra_dinkes_v1.pdf')",
    "INSERT INTO dokumen_bukti (id,dokumen_id,pemda_id,unit_id,tahun,judul) VALUES "
    "(1,1,1,1,2024,'SK Penetapan Renstra'),(2,2,1,1,2026,'Lampiran PK')",
]


async def main() -> None:
    path = os.path.abspath("local_esakip.db")
    if os.path.exists(path):
        os.remove(path)
    eng = create_async_engine(f"sqlite+aiosqlite:///{path}")
    async with eng.begin() as c:
        await c.execute(sqltext("PRAGMA journal_mode=WAL"))
        for stmt in filter(str.strip, SCHEMA_SQLITE_MINI.split(";")):
            await c.execute(sqltext(stmt))
        for stmt in SEED:
            await c.execute(sqltext(stmt))
    await buat_skema_agen(eng)
    await eng.dispose()
    print(f"OK: {path} siap (2 OPD: 1=DIKBUD, 2=DINKES; indikator 2025 & 2026).")


if __name__ == "__main__":
    asyncio.run(main())
