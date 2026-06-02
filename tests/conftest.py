"""Fixture bersama: paksa profil skema 'reference' tiap uji (hermetik dari .env).

Produksi memakai DB_SCHEMA_PROFILE=esakip, tetapi mayoritas uji memakai skema
referensi (SQLite). Fixture autouse ini menjamin uji tak terpengaruh nilai .env;
uji profil esakip meng-override dengan set_profile(EsakipProfile()) sendiri.
"""
from __future__ import annotations

import pytest

import metrics
from agent.llm import reset_llm_state
from db.profiles import reset_profile, set_profile
from db.profiles.reference import ReferenceProfile


@pytest.fixture(autouse=True)
def _profil_reference():
    set_profile(ReferenceProfile())
    reset_llm_state()  # cache & circuit breaker LLM bersih tiap uji
    metrics.reset()    # counter bersih tiap uji
    yield
    reset_profile()
