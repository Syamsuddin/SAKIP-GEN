"""Registry & pemilih profil skema aktif (via DB_SCHEMA_PROFILE)."""
from __future__ import annotations

from config import get_settings
from db.profiles.base import SchemaProfile

_active: SchemaProfile | None = None


def _tersedia() -> dict[str, SchemaProfile]:
    # Impor lokal agar tak ada siklus impor saat modul db.* dimuat.
    from db.profiles.esakip import EsakipProfile
    from db.profiles.reference import ReferenceProfile

    return {p.name: p for p in (ReferenceProfile(), EsakipProfile())}


def get_profile() -> SchemaProfile:
    """Profil aktif sesuai DB_SCHEMA_PROFILE (di-cache; dapat di-override untuk uji)."""
    global _active
    if _active is None:
        nama = get_settings().db_schema_profile
        tersedia = _tersedia()
        if nama not in tersedia:
            raise RuntimeError(
                f"DB_SCHEMA_PROFILE '{nama}' tak dikenal. Tersedia: {sorted(tersedia)}"
            )
        _active = tersedia[nama]
    return _active


def set_profile(profile: SchemaProfile) -> None:
    """Override profil aktif (dipakai pengujian)."""
    global _active
    _active = profile


def reset_profile() -> None:
    """Kembalikan ke pemilihan via konfigurasi."""
    global _active
    _active = None
