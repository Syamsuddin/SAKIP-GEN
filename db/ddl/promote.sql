-- ============================================================================
-- Fase 4 — penerapan ke tabel sumber. Tabel audit + kredensial PROMOTOR.
-- Promotor punya hak tulis PALING SEMPIT: hanya kolom tertentu pada `indikator`.
-- ============================================================================

CREATE TABLE IF NOT EXISTS ai_audit (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  usulan_id     BIGINT UNSIGNED NULL,
  aksi          VARCHAR(32)  NOT NULL,
  tabel_sasaran VARCHAR(64)  NOT NULL,
  kunci         VARCHAR(255) NOT NULL,
  data_sebelum  JSON         NULL,
  data_sesudah  JSON         NULL,
  oleh          VARCHAR(128) NOT NULL,
  pada          VARCHAR(32)  NOT NULL,
  PRIMARY KEY (id),
  KEY idx_usulan (usulan_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Jika tabel ai_usulan dibuat SEBELUM Fase 4 (tanpa kolom penerapan), jalankan:
--   ALTER TABLE ai_usulan ADD COLUMN diterapkan_oleh VARCHAR(128) NULL;
--   ALTER TABLE ai_usulan ADD COLUMN diterapkan_pada VARCHAR(32)  NULL;

-- Pengguna PROMOTOR: least privilege. Tidak ada akses tabel sumber lain.
CREATE USER IF NOT EXISTS 'sakip_promotor'@'localhost' IDENTIFIED BY 'GANTI_SANDI_KUAT';

-- Hanya kolom indikator tertentu yang boleh DIUBAH:
GRANT SELECT (id, kode, sasaran_id, uraian, satuan, tipologi),
      UPDATE (uraian, satuan, tipologi)
  ON sakip.indikator TO 'sakip_promotor'@'localhost';

-- Cukup baca untuk scoping OPD/tahun:
GRANT SELECT (id, opd_id, tahun) ON sakip.sasaran_strategis TO 'sakip_promotor'@'localhost';

-- Baca usulan + tandai diterapkan:
GRANT SELECT (id, status, payload, indikator_id, opd_id, tahun),
      UPDATE (status, diterapkan_oleh, diterapkan_pada)
  ON sakip.ai_usulan TO 'sakip_promotor'@'localhost';

-- Tulis jejak audit:
GRANT INSERT, SELECT ON sakip.ai_audit TO 'sakip_promotor'@'localhost';

FLUSH PRIVILEGES;

-- DSN: DB_PROMOTE_URL=mysql+asyncmy://sakip_promotor:GANTI_SANDI_KUAT@localhost/sakip
