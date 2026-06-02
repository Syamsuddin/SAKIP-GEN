"""Model Pydantic untuk Dosir Kinerja — kontrak data bersama SAKIP-Gen.

Bagian relevan untuk evaluasi Fase 1: meta, perencanaan, pengukuran, pelaporan,
dan evaluasi internal. Bagian 'perbaikan' (usulan) menyusul di Fase 3.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Capaian(BaseModel):
    indikator_id: str
    target: float | None = None
    realisasi: float | None = None
    persen_capaian: float | None = None


class Indikator(BaseModel):
    indikator_id: str
    uraian: str
    satuan: str | None = None
    tipologi: str | None = None  # input | proses | output | outcome | impact


class SasaranStrategis(BaseModel):
    kode: str
    uraian: str
    indikator: list[Indikator] = Field(default_factory=list)


class Perencanaan(BaseModel):
    sasaran_strategis: list[SasaranStrategis] = Field(default_factory=list)


class Pengukuran(BaseModel):
    capaian: list[Capaian] = Field(default_factory=list)


class Pelaporan(BaseModel):
    ada_lkjip: bool = False
    ada_analisis_capaian: bool = False
    ada_analisis_efisiensi: bool = False


class EvaluasiInternal(BaseModel):
    ada_evaluasi_internal: bool = False
    ada_tindak_lanjut: bool = False


class Meta(BaseModel):
    instansi: str
    opd_id: int
    tahun: int
    dibuat_pada: datetime


class DosirKinerja(BaseModel):
    meta: Meta
    perencanaan: Perencanaan = Field(default_factory=Perencanaan)
    pengukuran: Pengukuran = Field(default_factory=Pengukuran)
    pelaporan: Pelaporan = Field(default_factory=Pelaporan)
    evaluasi_internal: EvaluasiInternal = Field(default_factory=EvaluasiInternal)
