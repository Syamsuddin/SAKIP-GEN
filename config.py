# SPDX-License-Identifier: MIT
# SAKIP-Gen — Evaluator + Drafter untuk SAKIP PermenPAN-RB 88/2021
# Lihat LICENSE untuk detail MIT License.

"""Konfigurasi SAKIP-Gen (dibaca dari environment / file .env)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Wajib (Fase 0) ---
    bot_token: str
    webhook_secret: str
    public_base_url: str  # tanpa trailing slash, mis. https://app.contoh.id

    # --- Operasional ---
    set_webhook_on_startup: bool = True
    enable_scheduler: bool = True
    log_level: str = "INFO"
    env: str = "production"

    # --- Autentikasi (Fase 2) ---
    # JSON: {"KODE": {"nama": "...", "peran": "operator", "opd_ids": [1,2]}}
    registration_codes: str | None = None
    # CSV telegram_id yang otomatis berperan admin (akses bot tanpa /daftar).
    # mis. ADMIN_TELEGRAM_IDS=207118312,123456789
    admin_telegram_ids: str | None = None

    # --- Opsional (fase berikutnya) ---
    db_ro_url: str | None = None
    db_staging_url: str | None = None
    db_promote_url: str | None = None
    miniapp_base_url: str | None = None
    token_secret: str | None = None
    anthropic_api_key: str | None = None
    ollama_host: str | None = None

    # --- Hardening/observability (Fase 5) ---
    api_rate_per_menit: int = 30
    bot_rate_per_menit: int = 20
    max_body_bytes: int = 65536
    audit_to_db: bool = True
    # Bila diset, rate-limit API memakai Redis (konsisten lintas worker; lihat T5.1).
    redis_url: str | None = None

    # --- Fase 7 (auth SQL & LLM) ---
    use_sql_auth: bool = False
    llm_model: str | None = None

    # --- Profil skema sumber (adaptasi multi-eSAKIP) ---
    # "reference" = skema referensi (demo/uji); "esakip" = skema eSAKIP nyata.
    db_schema_profile: str = "reference"

    # --- Kalibrasi bobot LKE (Fase 2) ---
    # JSON override bobot komponen, mis. {"Capaian Kinerja": 40, "Perencanaan Kinerja": 18}.
    # Kosong = pakai BOBOT_DEFAULT (struktur Pengungkit 60 + Hasil 40).
    lke_bobot: str | None = None

    @property
    def admin_id_set(self) -> set[int]:
        """Himpunan telegram_id admin dari ADMIN_TELEGRAM_IDS (CSV; pemisah , atau ;)."""
        if not self.admin_telegram_ids:
            return set()
        out: set[int] = set()
        for bagian in self.admin_telegram_ids.replace(";", ",").split(","):
            bagian = bagian.strip()
            if bagian.lstrip("-").isdigit():
                out.add(int(bagian))
        return out

    @property
    def webhook_path(self) -> str:
        return f"/webhook/{self.webhook_secret}"

    @property
    def webhook_url(self) -> str:
        return f"{self.public_base_url.rstrip('/')}{self.webhook_path}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def audit_keamanan(s: "Settings") -> list[str]:
    """Daftar peringatan konfigurasi keamanan (non-fatal), diperiksa saat startup."""
    w: list[str] = []
    if s.env == "production":
        if len(s.webhook_secret) < 16:
            w.append("WEBHOOK_SECRET terlalu pendek (<16 karakter).")
        if not s.token_secret or len(s.token_secret) < 16:
            w.append("TOKEN_SECRET belum diset atau terlalu pendek (<16 karakter).")
        if not s.public_base_url.lower().startswith("https://"):
            w.append("PUBLIC_BASE_URL bukan HTTPS.")
        if not s.registration_codes and not s.admin_telegram_ids:
            w.append(
                "REGISTRATION_CODES & ADMIN_TELEGRAM_IDS kosong; tidak ada jalur akses bot."
            )
        if not s.use_sql_auth:
            w.append(
                "USE_SQL_AUTH=false — auth in-memory: pengguna terdaftar HILANG saat restart "
                "dan tak konsisten antar-worker. Aktifkan (USE_SQL_AUTH=true) untuk produksi."
            )
    return w
