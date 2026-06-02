"""Uji profil skema eSAKIP nyata: jalur BACA (Dosir) & TULIS (promosi) pada skema asli.

Memakai SCHEMA_SQLITE_MINI (subset kolom skema db/mysql/schema.sql) + seed setara demo,
agar pemetaan sakip_kinerja_node/sakip_indikator/sakip_target/realisasi/lkjip/evaluasi
tervalidasi tanpa MySQL. Sekaligus penjaga seam-drift untuk profil esakip.
"""
from __future__ import annotations

import pytest_asyncio
from sqlalchemy import text as sqltext
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool

from db.engines import set_promote_engine, set_ro_engine, set_staging_engine
from db.profiles import set_profile
from db.profiles.esakip import SCHEMA_SQLITE_MINI, EsakipProfile
from db.promote import AUDIT_SCHEMA_SQLITE, terapkan_usulan
from db.staging import STAGING_SCHEMA_SQLITE

_SEED = [
    "INSERT INTO unit_organisasi (id,kode_unit,nama,level_unit) VALUES (1,'DIKBUD','Dinas Pendidikan Kabupaten Seruyan','OPD')",
    "INSERT INTO ref_satuan (id,kode,nama) VALUES (1,'unit','Unit'),(2,'persen','Persen'),(3,'indeks','Indeks')",
    "INSERT INTO sakip_kinerja_node (id,unit_id,kode,uraian,jenis_node,status,tahun_awal,tahun_akhir) VALUES "
    "(1,1,'1','Meningkatnya mutu layanan pendidikan','SASARAN_OPD','AKTIF',2025,2027),"
    "(2,1,'2','Meningkatnya tata kelola pendidikan','SASARAN_OPD','AKTIF',2025,2027),"
    # Node Pemda (induk) & node unit/eselon (anak) untuk uji cascading
    "(100,99,'P1','Meningkatnya kualitas SDM daerah','SASARAN_PEMDA','AKTIF',2025,2027),"
    "(200,201,'1.1','Terlaksananya akreditasi sekolah','SASARAN_UNIT','AKTIF',2025,2027)",
    # Cascading: OPD(1) berkontribusi ke Pemda(100) [naik]; diturunkan ke unit(200) [turun]
    "INSERT INTO sakip_cascading_relasi (id,parent_node_id,child_node_id,jenis_relasi,bobot_kontribusi) VALUES "
    "(1,100,1,'KONTRIBUSI',60),(2,1,200,'TURUNAN_LANGSUNG',NULL)",
    "INSERT INTO sakip_indikator (id,node_id,kode,nama,satuan_id,jenis_indikator,status) VALUES "
    "(11,1,'IKU-1.1','Jumlah sekolah terakreditasi',1,'OUTPUT','AKTIF'),"
    "(12,1,'IKU-1.2','Persentase sekolah terakreditasi minimal B',2,'OUTCOME','AKTIF'),"
    "(13,2,'IKU-2.1','Indeks kepuasan layanan pendidikan',3,'OUTCOME','AKTIF'),"
    "(14,2,'IKU-2.2','Jumlah dokumen tata kelola disusun',1,'OUTPUT','AKTIF')",
    # Capaian TAHUNAN 2026 untuk 11,12,13 (14 sengaja kosong → gap pengukuran)
    "INSERT INTO sakip_target (id,indikator_id,tahun,periode,target_angka) VALUES "
    "(1,11,2026,'TAHUNAN',120),(2,12,2026,'TAHUNAN',80),(3,13,2026,'TAHUNAN',85)",
    "INSERT INTO sakip_realisasi (id,indikator_id,tahun,periode,realisasi_angka) VALUES "
    "(1,11,2026,'TAHUNAN',96),(2,12,2026,'TAHUNAN',72),(3,13,2026,'TAHUNAN',83)",
    # Capaian TRIWULAN_2 2026 untuk 11,12 (13 sengaja kosong di TW2 → hanya 2 baris)
    "INSERT INTO sakip_target (id,indikator_id,tahun,periode,target_angka) VALUES "
    "(11,11,2026,'TRIWULAN_2',60),(12,12,2026,'TRIWULAN_2',40)",
    "INSERT INTO sakip_realisasi (id,indikator_id,tahun,periode,realisasi_angka) VALUES "
    "(11,11,2026,'TRIWULAN_2',30),(12,12,2026,'TRIWULAN_2',38)",
    # Pelaporan: ada LKjIP + analisis capaian, TANPA analisis efisiensi
    "INSERT INTO lkjip_dokumen (id,unit_id,tahun) VALUES (1,1,2026)",
    "INSERT INTO lkjip_capaian (id,lkjip_id,narasi_analisis,narasi_efisiensi) VALUES (1,1,'Analisis capaian tersedia',NULL)",
    # Evaluasi internal ADA
    "INSERT INTO evaluasi_akip (id,tahun,jenis_evaluasi) VALUES (1,2026,'INTERNAL_INSPEKTORAT')",
    "INSERT INTO evaluasi_unit (id,evaluasi_id,unit_id) VALUES (1,1,1)",
    # Temuan → rekomendasi → tindak lanjut
    "INSERT INTO evaluasi_temuan (id,evaluasi_unit_id,jenis_temuan,uraian,tingkat_risiko) VALUES "
    "(1,1,'KELEMAHAN','Indikator belum berorientasi hasil','SEDANG')",
    "INSERT INTO evaluasi_rekomendasi (id,temuan_id,rekomendasi,prioritas,status) VALUES "
    "(1,1,'Rumuskan ulang IKU ke outcome','TINGGI','DITINDAKLANJUTI')",
    "INSERT INTO evaluasi_tindak_lanjut (id,rekomendasi_id,uraian_tindak_lanjut,progres_persen,status) VALUES "
    "(1,1,'Draft IKU outcome disusun',60,'DIAJUKAN')",
    # Dokumen SAKIP OPD 1: RENSTRA (2 versi, 1 bukti) + PK (1 versi, tanpa bukti)
    "INSERT INTO ref_dokumen_jenis (id,kode,nama,kelompok,level_dokumen) VALUES "
    "(1,'RENSTRA','Rencana Strategis Perangkat Daerah','PERENCANAAN','OPD'),"
    "(2,'PK','Perjanjian Kinerja','PENGUKURAN','OPD'),"
    "(3,'LKJIP_OPD','Laporan Kinerja Perangkat Daerah','PELAPORAN','OPD')",
    "INSERT INTO dokumen (id,pemda_id,unit_id,jenis_dokumen_id,tahun,nomor_dokumen,judul,status) VALUES "
    "(1,1,1,1,2025,'050/123','Renstra Dinas Pendidikan 2025-2027','DITETAPKAN'),"
    "(2,1,1,2,2026,'PK/2026','Perjanjian Kinerja 2026','DITETAPKAN')",
    "INSERT INTO dokumen_versi (id,dokumen_id,versi,nama_file) VALUES "
    "(1,1,1,'renstra_v1.pdf'),(2,1,2,'renstra_v2.pdf'),(3,2,1,'pk_2026.pdf')",
    "INSERT INTO dokumen_bukti (id,dokumen_id,pemda_id,unit_id,tahun,judul) VALUES "
    "(1,1,1,1,2025,'SK Penetapan Renstra')",
]


@pytest_asyncio.fixture
async def esakip_db():
    eng = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with eng.begin() as conn:
        for skema in (SCHEMA_SQLITE_MINI, STAGING_SCHEMA_SQLITE, AUDIT_SCHEMA_SQLITE):
            for stmt in filter(str.strip, skema.split(";")):
                await conn.execute(sqltext(stmt))
        for stmt in _SEED:
            await conn.execute(sqltext(stmt))
    set_ro_engine(eng)
    set_staging_engine(eng)
    set_promote_engine(eng)
    set_profile(EsakipProfile())
    yield eng
    await eng.dispose()


def _skor(hasil, nama: str) -> float:
    return next(k.skor for k in hasil.komponen if k.nama == nama)


async def test_bangun_dosir_esakip(esakip_db):
    from agent.service import evaluasi_opd

    dosir, hasil = await evaluasi_opd(1, 2026)

    assert "Dinas Pendidikan" in hasil.instansi
    ind = [i for s in dosir.perencanaan.sasaran_strategis for i in s.indikator]
    assert len(ind) == 4
    assert sum(1 for i in ind if i.tipologi in {"outcome", "impact"}) == 2
    # indikator_id = PK sakip_indikator (string)
    assert {i.indikator_id for i in ind} == {"11", "12", "13", "14"}

    # Sub-skor komponen (0..100) — tak terpengaruh perubahan bobot Fase 2.
    assert _skor(hasil, "Perencanaan Kinerja") == 70.0
    assert _skor(hasil, "Pengukuran Kinerja") == 75.0          # 3/4 indikator terukur
    assert _skor(hasil, "Pelaporan Kinerja") == 80.0           # lkjip + analisis, tanpa efisiensi
    assert _skor(hasil, "Evaluasi Akuntabilitas Kinerja Internal") == 100.0  # eval ya, TL ya (seed temuan)
    # Komponen HASIL: capaian aktual (80, 90, 97.65, 0 untuk IKU-2.2 tak terukur) → 66.91.
    assert _skor(hasil, "Capaian Kinerja") == 66.91
    # Total berbobot (kalibrasi 88/2021: Peren 18, Peng 18, Pel 9, Eval 15, Hasil 40):
    # 12.6 + 13.5 + 7.2 + 15.0 + 26.76 = 75.06 → BB.
    assert hasil.nilai_total == 75.06 and hasil.predikat == "BB"

    assert dosir.pelaporan.ada_lkjip is True
    assert dosir.pelaporan.ada_analisis_capaian is True
    assert dosir.pelaporan.ada_analisis_efisiensi is False
    assert dosir.evaluasi_internal.ada_evaluasi_internal is True
    assert dosir.evaluasi_internal.ada_tindak_lanjut is True   # ada rantai tindak lanjut (seed)


async def test_promote_esakip_round_trip(esakip_db):
    """BACA→usul→setujui→TULIS pada skema eSAKIP; perubahan terbaca ulang (anti seam-drift)."""
    from agent.improver import usulkan_perbaikan_indikator
    from agent.service import evaluasi_opd
    from db.staging import putuskan_usulan, simpan_draft

    dosir, hasil = await evaluasi_opd(1, 2026)
    # IKU-1.1 (PK 11) bertipologi output → usulkan ke outcome.
    u = usulkan_perbaikan_indikator(dosir, hasil, "11")
    assert u is not None
    uraian_baru = next(p.usulan for p in u.perubahan if p.field == "uraian")
    uid = await simpan_draft(u)
    await putuskan_usulan(uid, ditinjau_oleh="Andi", status="disetujui")

    res = await terapkan_usulan(uid, oleh="Kadis")
    assert res.ok, res.pesan
    assert res.sebelum["tipologi"] == "output" and res.sesudah["tipologi"] == "outcome"
    assert "uraian" in res.field_diterapkan and "tipologi" in res.field_diterapkan
    assert "satuan" in res.field_diabaikan          # satuan FK belum dipromosikan profil esakip

    # Verifikasi kolom fisik sakip_indikator benar-benar berubah.
    async with esakip_db.connect() as conn:
        row = (await conn.execute(
            sqltext("SELECT nama, jenis_indikator FROM sakip_indikator WHERE id = 11")
        )).mappings().first()
    assert row["jenis_indikator"] == "OUTCOME"
    assert row["nama"] == uraian_baru

    # BACA ulang: evaluator melihat perubahan → Perencanaan naik 70 → 85.
    _, sesudah = await evaluasi_opd(1, 2026)
    assert _skor(sesudah, "Perencanaan Kinerja") == 85.0


async def test_temuan_esakip(esakip_db):
    """Profil esakip membaca temuan → rekomendasi → tindak lanjut dari skema sumber."""
    from agent.service import temuan_opd

    daftar = await temuan_opd(1, 2026)
    assert len(daftar) == 1
    t = daftar[0]
    assert t.jenis == "KELEMAHAN" and "berorientasi hasil" in t.uraian and t.tingkat_risiko == "SEDANG"
    assert len(t.rekomendasi) == 1
    r = t.rekomendasi[0]
    assert "outcome" in r.uraian and r.prioritas == "TINGGI" and r.status == "DITINDAKLANJUTI"
    assert r.progres == 60 and r.tindak_lanjut == "DIAJUKAN"
    # OPD tanpa evaluasi internal → kosong.
    assert await temuan_opd(2, 2026) == []


async def test_capaian_periode_esakip(esakip_db):
    """Profil esakip membaca capaian per periode (TW2) dari sakip_target/realisasi."""
    from agent.service import capaian_periode

    tw2 = await capaian_periode(1, 2026, "tw2")
    # Hanya 11 & 12 punya data TW2 (13 & 14 kosong di periode itu).
    assert {c.indikator_id for c in tw2} == {"11", "12"}
    c11 = next(c for c in tw2 if c.indikator_id == "11")
    assert c11.target == 60 and c11.realisasi == 30 and c11.persen_capaian == 50.0
    c12 = next(c for c in tw2 if c.indikator_id == "12")
    assert c12.persen_capaian == 95.0
    # Periode tanpa data → [] (anti-gagal; pemanggil fallback ke tahunan).
    assert await capaian_periode(1, 2026, "tw3") == []


async def test_capaian_periode_reference_kosong():
    """Profil referensi tak punya data periodik → [] (capaian disajikan tahunan)."""
    from db.profiles.reference import ReferenceProfile

    assert await ReferenceProfile().ambil_capaian(1, 2026, "tw2") == []


async def test_dokumen_esakip(esakip_db):
    """Profil esakip menelusur dokumen OPD: jenis, versi terakhir, jumlah bukti."""
    from agent.service import dokumen_opd

    semua = await dokumen_opd(1)
    assert {d.jenis for d in semua} == {"RENSTRA", "PK"}
    renstra = next(d for d in semua if d.jenis == "RENSTRA")
    assert renstra.jumlah_versi == 2 and renstra.versi_terakhir == 2 and renstra.jumlah_bukti == 1
    pk = next(d for d in semua if d.jenis == "PK")
    assert pk.jumlah_versi == 1 and pk.jumlah_bukti == 0

    # Saring per jenis kanonik.
    hanya_pk = await dokumen_opd(1, jenis="pk")
    assert len(hanya_pk) == 1 and hanya_pk[0].jenis == "PK"
    # Saring per tahun.
    thn2026 = await dokumen_opd(1, tahun=2026)
    assert {d.jenis for d in thn2026} == {"PK"}
    # `pohon` bukan dokumen → kosong; OPD tanpa dokumen → kosong.
    assert await dokumen_opd(1, jenis="pohon") == []
    assert await dokumen_opd(2) == []


async def test_dokumen_reference_kosong():
    """Profil referensi tak punya modul dokumen → [] (anti-gagal)."""
    from db.profiles.reference import ReferenceProfile

    assert await ReferenceProfile().ambil_dokumen(1, 2026, None) == []


async def test_cascading_esakip(esakip_db):
    """Profil esakip membaca keselarasan pohon kinerja: arah naik (ke Pemda) & turun (ke unit)."""
    from agent.service import cascading_opd

    rel = await cascading_opd(1, 2026)
    assert len(rel) == 2
    naik = next(r for r in rel if r.arah == "naik")
    assert naik.parent == "Meningkatnya kualitas SDM daerah" and naik.jenis == "KONTRIBUSI"
    assert naik.bobot == 60
    turun = next(r for r in rel if r.arah == "turun")
    assert turun.child == "Terlaksananya akreditasi sekolah" and turun.jenis == "TURUNAN_LANGSUNG"
    # OPD tanpa relasi cascading → kosong.
    assert await cascading_opd(2, 2026) == []


async def test_cascading_reference_kosong():
    """Profil referensi tak punya relasi cascading → [] (keselarasan via heuristik)."""
    from db.profiles.reference import ReferenceProfile

    assert await ReferenceProfile().ambil_cascading(1, 2026) == []


async def test_temuan_reference_kosong():
    """Profil referensi (skema mainan) tak punya modul evaluasi internal → [] (anti-gagal)."""
    from db.profiles.reference import ReferenceProfile

    assert await ReferenceProfile().ambil_temuan(1, 2026) == []
