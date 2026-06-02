-- ============================================================================
-- GRANT least-privilege untuk profil skema "esakip" (DB_SCHEMA_PROFILE=esakip).
-- Selaras db/profiles/esakip.py. Sesuaikan nama skema `sakip`, host, dan sandi.
--
-- Tiga kredensial terpisah (bukan flag aplikasi):
--   sakip_ro        : analitik read-only (membangun Dosir)
--   sakip_staging   : tabel milik agen (ai_usulan / ai_event[/auth])
--   sakip_promotor  : tulis paling sempit ke sakip_indikator (kolom tertentu)
-- ============================================================================

-- ---------- RO: hanya SELECT pada tabel sumber yang dibaca profil esakip ----------
CREATE USER IF NOT EXISTS 'sakip_ro'@'127.0.0.1' IDENTIFIED BY 'GANTI_SANDI_KUAT';
GRANT SELECT ON sakip.unit_organisasi        TO 'sakip_ro'@'127.0.0.1';
GRANT SELECT ON sakip.ref_satuan             TO 'sakip_ro'@'127.0.0.1';
GRANT SELECT ON sakip.sakip_kinerja_node     TO 'sakip_ro'@'127.0.0.1';
GRANT SELECT ON sakip.sakip_indikator        TO 'sakip_ro'@'127.0.0.1';
GRANT SELECT ON sakip.sakip_target           TO 'sakip_ro'@'127.0.0.1';
GRANT SELECT ON sakip.sakip_realisasi        TO 'sakip_ro'@'127.0.0.1';
GRANT SELECT ON sakip.lkjip_dokumen          TO 'sakip_ro'@'127.0.0.1';
GRANT SELECT ON sakip.lkjip_capaian          TO 'sakip_ro'@'127.0.0.1';
GRANT SELECT ON sakip.evaluasi_akip          TO 'sakip_ro'@'127.0.0.1';
GRANT SELECT ON sakip.evaluasi_unit          TO 'sakip_ro'@'127.0.0.1';
GRANT SELECT ON sakip.evaluasi_temuan        TO 'sakip_ro'@'127.0.0.1';
GRANT SELECT ON sakip.evaluasi_rekomendasi   TO 'sakip_ro'@'127.0.0.1';
GRANT SELECT ON sakip.evaluasi_tindak_lanjut TO 'sakip_ro'@'127.0.0.1';
-- (opsional, untuk fase berikutnya / Komponen Hasil):
-- GRANT SELECT ON sakip.anggaran_pagu, sakip.anggaran_realisasi, sakip.sakip_capaian,
--                 sakip.ref_predikat_sakip TO 'sakip_ro'@'127.0.0.1';

-- ---------- STAGING: hanya tabel milik agen ----------
CREATE USER IF NOT EXISTS 'sakip_staging'@'127.0.0.1' IDENTIFIED BY 'GANTI_SANDI_KUAT';
GRANT INSERT, SELECT, UPDATE ON sakip.ai_usulan TO 'sakip_staging'@'127.0.0.1';
GRANT INSERT, SELECT          ON sakip.ai_event  TO 'sakip_staging'@'127.0.0.1';
-- Bila USE_SQL_AUTH=true:
-- GRANT INSERT, SELECT, UPDATE ON sakip.bot_users TO 'sakip_staging'@'127.0.0.1';
-- GRANT INSERT, SELECT, UPDATE ON sakip.registration_codes TO 'sakip_staging'@'127.0.0.1';

-- ---------- PROMOTOR: tulis PALING SEMPIT ke sakip_indikator ----------
-- Profil esakip hanya mempromosikan {uraian->nama, tipologi->jenis_indikator}.
CREATE USER IF NOT EXISTS 'sakip_promotor'@'127.0.0.1' IDENTIFIED BY 'GANTI_SANDI_KUAT';
GRANT SELECT (id, node_id, kode, nama, satuan_id, jenis_indikator),
      UPDATE (nama, jenis_indikator)
  ON sakip.sakip_indikator TO 'sakip_promotor'@'127.0.0.1';
GRANT SELECT (id, kode) ON sakip.ref_satuan TO 'sakip_promotor'@'127.0.0.1';
-- Baca usulan + tandai diterapkan + tulis audit (tabel milik agen):
GRANT SELECT (id, status, payload, indikator_id, opd_id, tahun),
      UPDATE (status, diterapkan_oleh, diterapkan_pada)
  ON sakip.ai_usulan TO 'sakip_promotor'@'127.0.0.1';
GRANT INSERT, SELECT ON sakip.ai_audit TO 'sakip_promotor'@'127.0.0.1';

FLUSH PRIVILEGES;

-- DSN (asyncmy):
--   DB_RO_URL=mysql+asyncmy://sakip_ro:GANTI_SANDI_KUAT@127.0.0.1/sakip
--   DB_STAGING_URL=mysql+asyncmy://sakip_staging:GANTI_SANDI_KUAT@127.0.0.1/sakip
--   DB_PROMOTE_URL=mysql+asyncmy://sakip_promotor:GANTI_SANDI_KUAT@127.0.0.1/sakip
