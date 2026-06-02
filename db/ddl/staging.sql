-- ============================================================================
-- Skema staging usulan SAKIP-Gen (MySQL 8). Tabel ai_usulan MILIK agen.
-- Promosi ke tabel sumber dilakukan TERPISAH oleh aplikasi SAKIP / manusia
-- dengan kredensial berbeda. Stempel waktu = string ISO-8601 UTC (VARCHAR).
-- ============================================================================

CREATE TABLE IF NOT EXISTS ai_usulan (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  tipe            VARCHAR(64)  NOT NULL DEFAULT 'perbaikan_indikator',
  instansi        VARCHAR(255) NULL,
  opd_id          INT          NOT NULL,
  level           ENUM('dinas','bidang','seksi') NOT NULL DEFAULT 'dinas',
  unit            VARCHAR(255) NULL,
  indikator_id    VARCHAR(64)  NULL,
  tahun           SMALLINT     NOT NULL,
  payload         JSON         NOT NULL,
  gap_lke         VARCHAR(128) NULL,
  estimasi_poin   DECIMAL(6,2) NOT NULL DEFAULT 0,
  hash_data_lama  CHAR(64)     NOT NULL,
  status          ENUM('draft','disetujui','ditolak','diterapkan') NOT NULL DEFAULT 'draft',
  disusun_oleh    VARCHAR(64)  NOT NULL DEFAULT 'agen',
  ditinjau_oleh   VARCHAR(128) NULL,
  dibuat_pada     VARCHAR(32)  NOT NULL,
  diputuskan_pada VARCHAR(32)  NULL,
  diterapkan_oleh VARCHAR(128) NULL,
  diterapkan_pada VARCHAR(32)  NULL,
  PRIMARY KEY (id),
  KEY idx_opd_tahun (opd_id, tahun),
  KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Pengguna staging: HANYA tabel ai_usulan, tanpa akses tabel sumber apa pun.
-- (sesuaikan nama skema `sakip`, host, dan sandi dengan lingkungan Anda)
CREATE USER IF NOT EXISTS 'sakip_staging'@'localhost' IDENTIFIED BY 'GANTI_SANDI_KUAT';
GRANT INSERT, SELECT, UPDATE ON sakip.ai_usulan TO 'sakip_staging'@'localhost';
FLUSH PRIVILEGES;

-- Contoh DSN async (asyncmy):
--   DB_STAGING_URL=mysql+asyncmy://sakip_staging:GANTI_SANDI_KUAT@localhost/sakip
