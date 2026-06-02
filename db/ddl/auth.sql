-- ============================================================================
-- Fase 7 — autentikasi berbasis SQL. Tabel milik agen (engine staging).
-- Aktifkan dengan USE_SQL_AUTH=true di .env.
-- ============================================================================
CREATE TABLE IF NOT EXISTS bot_users (
  telegram_id BIGINT       NOT NULL,
  nama        VARCHAR(128) NULL,
  peran       VARCHAR(32)  NOT NULL DEFAULT 'operator',
  opd_ids     JSON         NULL,
  dibuat_pada VARCHAR(32)  NULL,
  PRIMARY KEY (telegram_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS registration_codes (
  kode         VARCHAR(64)  NOT NULL,
  nama         VARCHAR(128) NULL,
  peran        VARCHAR(32)  NOT NULL DEFAULT 'operator',
  opd_ids      JSON         NULL,
  dipakai      TINYINT      NOT NULL DEFAULT 0,
  dipakai_oleh BIGINT       NULL,
  dipakai_pada VARCHAR(32)  NULL,
  PRIMARY KEY (kode)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Pengguna staging mengelola tabel auth:
GRANT SELECT, INSERT, UPDATE, DELETE ON sakip.bot_users TO 'sakip_staging'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON sakip.registration_codes TO 'sakip_staging'@'localhost';
FLUSH PRIVILEGES;

-- Menerbitkan kode (contoh):
-- INSERT INTO registration_codes (kode, nama, peran, opd_ids)
-- VALUES ('KADIS-2026', 'Kepala Dinas', 'kepala_dinas', JSON_ARRAY(1));
