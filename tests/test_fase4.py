"""Uji Fase 4: penerapan usulan ke tabel sumber, pengaman, audit, dan RBAC promosi."""
from __future__ import annotations

import pytest_asyncio
from sqlalchemy import text as sqltext

from db.engines import set_promote_engine, set_ro_engine, set_staging_engine
from db.promote import AUDIT_SCHEMA_SQLITE, terapkan_usulan
from db.staging import STAGING_SCHEMA_SQLITE
from demo_evaluasi import build_demo_engine


@pytest_asyncio.fixture
async def combined_db():
    """Satu engine SQLite berisi tabel sumber + ai_usulan + ai_audit (meniru satu MySQL)."""
    eng = await build_demo_engine()
    async with eng.begin() as conn:
        for stmt in filter(str.strip, STAGING_SCHEMA_SQLITE.split(";")):
            await conn.execute(sqltext(stmt))
        for stmt in filter(str.strip, AUDIT_SCHEMA_SQLITE.split(";")):
            await conn.execute(sqltext(stmt))
    set_ro_engine(eng)
    set_staging_engine(eng)
    set_promote_engine(eng)
    yield eng
    await eng.dispose()


async def _draft_disetujui(indikator_kode: str):
    from agent.improver import usulkan_dari_gap
    from agent.service import evaluasi_opd
    from db.staging import putuskan_usulan, simpan_draft

    dosir, hasil = await evaluasi_opd(1, 2026)
    u = next(k for k in usulkan_dari_gap(dosir, hasil, maksimal=9) if k.indikator_id == indikator_kode)
    uid = await simpan_draft(u)
    await putuskan_usulan(uid, ditinjau_oleh="Andi", status="disetujui")
    return u, uid


async def test_terapkan_happy(combined_db):
    from db.staging import ambil_usulan

    u, uid = await _draft_disetujui("IKU-1.1")
    uraian_baru = next(p.usulan for p in u.perubahan if p.field == "uraian")

    hasil = await terapkan_usulan(uid, oleh="Kadis")
    assert hasil.ok, hasil.pesan
    assert hasil.sebelum["tipologi"] == "output"
    assert hasil.sesudah["tipologi"] == "outcome"
    assert "tipologi" in hasil.field_diterapkan and "uraian" in hasil.field_diterapkan

    async with combined_db.connect() as conn:
        row = (await conn.execute(
            sqltext("SELECT uraian, tipologi, satuan FROM indikator WHERE kode='IKU-1.1'")
        )).mappings().first()
    assert row["tipologi"] == "outcome"
    assert row["uraian"] == uraian_baru

    u_after = await ambil_usulan(uid)
    assert u_after.status == "diterapkan" and u_after.diterapkan_oleh == "Kadis"

    async with combined_db.connect() as conn:
        n = (await conn.execute(
            sqltext("SELECT COUNT(*) FROM ai_audit WHERE usulan_id = :i"), {"i": uid}
        )).scalar()
    assert n == 1

    # Idempoten-aman: penerapan ulang ditolak karena status sudah 'diterapkan'.
    lagi = await terapkan_usulan(uid, oleh="Kadis")
    assert not lagi.ok and "disetujui" in lagi.pesan.lower()


async def test_terapkan_belum_disetujui(combined_db):
    from agent.improver import usulkan_dari_gap
    from agent.service import evaluasi_opd
    from db.staging import simpan_draft

    dosir, hasil = await evaluasi_opd(1, 2026)
    u = usulkan_dari_gap(dosir, hasil, maksimal=1)[0]
    uid = await simpan_draft(u)  # tetap 'draft'
    res = await terapkan_usulan(uid, oleh="Kadis")
    assert not res.ok and "disetujui" in res.pesan.lower()


async def test_terapkan_data_basi(combined_db):
    _, uid = await _draft_disetujui("IKU-2.2")
    async with combined_db.begin() as conn:
        await conn.execute(sqltext("UPDATE indikator SET uraian='Diubah manual' WHERE kode='IKU-2.2'"))
    res = await terapkan_usulan(uid, oleh="Kadis")
    assert not res.ok and "berubah" in res.pesan.lower()


async def test_terapkan_tidak_ada(combined_db):
    res = await terapkan_usulan(999999, oleh="Kadis")
    assert not res.ok and "tidak ditemukan" in res.pesan.lower()


async def test_seam_konsistensi_baca_tulis(combined_db):
    """T1.1 — jalur BACA (db/queries.py) & TULIS (db/promote.py) konsisten pada satu skema.

    Perubahan yang diterapkan promotor harus terbaca ulang oleh evaluator. Bila nama
    tabel/kolom antara kedua file menyimpang (seam-drift), uji ini gagal.
    """
    from agent.service import evaluasi_opd

    def skor_perencanaan(hasil) -> float:
        return next(k.skor for k in hasil.komponen if k.nama == "Perencanaan Kinerja")

    # Sebelum: 2 dari 4 indikator berorientasi hasil → 40 + 60·(2/4) = 70.
    _, sebelum = await evaluasi_opd(1, 2026)
    assert skor_perencanaan(sebelum) == 70.0

    # TULIS: terapkan usulan output→outcome untuk IKU-1.1 lewat jalur promosi.
    _, uid = await _draft_disetujui("IKU-1.1")
    res = await terapkan_usulan(uid, oleh="Kadis")
    assert res.ok, res.pesan

    # BACA ulang: evaluator melihat perubahan jalur TULIS pada kolom yang sama.
    _, sesudah = await evaluasi_opd(1, 2026)
    assert skor_perencanaan(sesudah) == 85.0  # kini 3 dari 4 → 40 + 60·(3/4)
    detail_perencanaan = [
        d for g in sesudah.gap if g.komponen == "Perencanaan Kinerja" for d in g.detail
    ]
    assert not any("IKU-1.1" in d for d in detail_perencanaan)


def test_boleh_promosi():
    from bot.auth import User

    assert User(1, "A", "operator", [1]).boleh_promosi() is False
    assert User(2, "B", "kepala_dinas", [1]).boleh_promosi() is True
    assert User(3, "C", "admin", []).boleh_promosi() is True
