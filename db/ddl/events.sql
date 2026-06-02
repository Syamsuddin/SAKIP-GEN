-- ============================================================================
-- Fase 5 — event log (audit aktivitas/keamanan). Beda dari ai_audit (data sumber).
-- ============================================================================
CREATE TABLE IF NOT EXISTS ai_event (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  pada        VARCHAR(32)  NOT NULL,
  kategori    VARCHAR(32)  NOT NULL,
  aksi        VARCHAR(64)  NOT NULL,
  telegram_id BIGINT       NULL,
  nama        VARCHAR(128) NULL,
  peran       VARCHAR(32)  NULL,
  opd_id      INT          NULL,
  status      VARCHAR(16)  NULL,
  ringkas     VARCHAR(255) NULL,
  request_id  VARCHAR(32)  NULL,
  detail      JSON         NULL,
  PRIMARY KEY (id),
  KEY idx_kategori (kategori),
  KEY idx_telegram (telegram_id),
  KEY idx_pada (pada)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Pengguna staging juga menulis event log:
GRANT INSERT, SELECT ON sakip.ai_event TO 'sakip_staging'@'localhost';
FLUSH PRIVILEGES;
