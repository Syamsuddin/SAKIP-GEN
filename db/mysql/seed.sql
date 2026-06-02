-- SEED.sql
-- Data seed minimal simulasi SAKIP Pemda level kabupaten untuk 1 siklus tahunan
-- Target: MySQL 8.0+
-- Prasyarat: jalankan DDL SAKIP terlebih dahulu

USE sakip_pemda;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 1;

SET @tahun := 2026;
SET @tahun_awal_rpjmd := 2025;
SET @tahun_akhir_rpjmd := 2029;

START TRANSACTION;

-- =========================================================
-- 1. REFERENSI DASAR
-- =========================================================

INSERT IGNORE INTO ref_tahun (tahun, nama_tahun, is_aktif) VALUES
(2025, '2025', 1),
(2026, '2026', 1),
(2027, '2027', 1),
(2028, '2028', 1),
(2029, '2029', 1);

INSERT IGNORE INTO ref_satuan (kode, nama, tipe) VALUES
('PERSEN', 'Persen', 'PERSEN'),
('RUPIAH', 'Rupiah', 'RUPIAH'),
('INDEKS', 'Indeks', 'INDEKS'),
('NILAI', 'Nilai', 'JUMLAH'),
('ORANG', 'Orang', 'JUMLAH'),
('DOKUMEN', 'Dokumen', 'JUMLAH'),
('SEKOLAH', 'Sekolah', 'JUMLAH'),
('PREDIKAT', 'Predikat', 'PREDIKAT');

INSERT IGNORE INTO ref_predikat_sakip (kode, nama, nilai_min, nilai_max, uraian) VALUES
('AA', 'Sangat Memuaskan', 90.01, 100.00, 'Akuntabilitas kinerja sangat baik'),
('A', 'Memuaskan', 80.01, 90.00, 'Akuntabilitas kinerja baik'),
('BB', 'Sangat Baik', 70.01, 80.00, 'Akuntabilitas kinerja sangat baik pada sebagian besar area'),
('B', 'Baik', 60.01, 70.00, 'Akuntabilitas kinerja baik namun masih perlu penguatan'),
('CC', 'Cukup', 50.01, 60.00, 'Akuntabilitas kinerja cukup'),
('C', 'Kurang', 30.01, 50.00, 'Akuntabilitas kinerja kurang'),
('D', 'Sangat Kurang', 0.00, 30.00, 'Akuntabilitas kinerja sangat kurang');

INSERT IGNORE INTO ref_dokumen_jenis (kode, nama, kelompok, level_dokumen) VALUES
('RPJMD', 'Rencana Pembangunan Jangka Menengah Daerah', 'PERENCANAAN', 'PEMDA'),
('RKPD', 'Rencana Kerja Pemerintah Daerah', 'PERENCANAAN', 'PEMDA'),
('RENSTRA', 'Rencana Strategis Perangkat Daerah', 'PERENCANAAN', 'OPD'),
('RENJA', 'Rencana Kerja Perangkat Daerah', 'PERENCANAAN', 'OPD'),
('IKU', 'Indikator Kinerja Utama', 'PENGUKURAN', 'OPD'),
('PK', 'Perjanjian Kinerja', 'PENGUKURAN', 'OPD'),
('RENAKSI', 'Rencana Aksi Kinerja', 'PENGUKURAN', 'OPD'),
('LKJIP_PEMDA', 'Laporan Kinerja Instansi Pemerintah Daerah', 'PELAPORAN', 'PEMDA'),
('LKJIP_OPD', 'Laporan Kinerja Perangkat Daerah', 'PELAPORAN', 'OPD'),
('LKE', 'Lembar Kerja Evaluasi AKIP', 'EVALUASI', 'OPD'),
('LHE', 'Laporan Hasil Evaluasi AKIP', 'EVALUASI', 'OPD'),
('BUKTI_DUKUNG', 'Bukti Dukung SAKIP', 'BUKTI', 'UMUM');

INSERT IGNORE INTO ref_regulasi (kode, nama, nomor, tahun, jenis, status_berlaku) VALUES
('PERPRES_29_2014', 'Sistem Akuntabilitas Kinerja Instansi Pemerintah', '29', 2014, 'PERPRES', 'BERLAKU'),
('PERMENPANRB_53_2014', 'Petunjuk Teknis Perjanjian Kinerja, Pelaporan Kinerja dan Tata Cara Reviu atas Laporan Kinerja Instansi Pemerintah', '53', 2014, 'PERMEN', 'BERLAKU'),
('PERMENPANRB_88_2021', 'Evaluasi Akuntabilitas Kinerja Instansi Pemerintah', '88', 2021, 'PERMEN', 'BERLAKU'),
('PERMENPANRB_89_2021', 'Penjenjangan Kinerja Instansi Pemerintah', '89', 2021, 'PERMEN', 'BERLAKU'),
('PERMENDAGRI_86_2017', 'Tata Cara Perencanaan, Pengendalian dan Evaluasi Pembangunan Daerah', '86', 2017, 'PERMEN', 'BERLAKU');

-- =========================================================
-- 2. REFERENSI URUSAN, PROGRAM, KEGIATAN, SUB KEGIATAN
-- =========================================================

INSERT IGNORE INTO ref_urusan (kode, nama, jenis) VALUES
('1.01', 'Pendidikan', 'WAJIB_PELAYANAN_DASAR');

SET @urusan_pendidikan_id := (SELECT id FROM ref_urusan WHERE kode = '1.01' LIMIT 1);

INSERT IGNORE INTO ref_bidang_urusan (urusan_id, kode, nama) VALUES
(@urusan_pendidikan_id, '1.01.01', 'Bidang Urusan Pendidikan');

SET @bidang_pendidikan_id := (SELECT id FROM ref_bidang_urusan WHERE kode = '1.01.01' LIMIT 1);

INSERT IGNORE INTO ref_program (bidang_urusan_id, kode, nama) VALUES
(@bidang_pendidikan_id, '1.01.02', 'Program Pengelolaan Pendidikan');

SET @program_pendidikan_id := (SELECT id FROM ref_program WHERE kode = '1.01.02' LIMIT 1);

INSERT IGNORE INTO ref_kegiatan (program_id, kode, nama) VALUES
(@program_pendidikan_id, '1.01.02.2.01', 'Pengelolaan Pendidikan Sekolah Dasar'),
(@program_pendidikan_id, '1.01.02.2.02', 'Pengelolaan Pendidikan Sekolah Menengah Pertama');

SET @kegiatan_sd_id := (SELECT id FROM ref_kegiatan WHERE kode = '1.01.02.2.01' LIMIT 1);
SET @kegiatan_smp_id := (SELECT id FROM ref_kegiatan WHERE kode = '1.01.02.2.02' LIMIT 1);

INSERT IGNORE INTO ref_sub_kegiatan (kegiatan_id, kode, nama) VALUES
(@kegiatan_sd_id, '1.01.02.2.01.0001', 'Penyediaan Layanan Pendidikan Sekolah Dasar'),
(@kegiatan_smp_id, '1.01.02.2.02.0001', 'Penyediaan Layanan Pendidikan Sekolah Menengah Pertama');

SET @sub_sd_id := (SELECT id FROM ref_sub_kegiatan WHERE kode = '1.01.02.2.01.0001' LIMIT 1);
SET @sub_smp_id := (SELECT id FROM ref_sub_kegiatan WHERE kode = '1.01.02.2.02.0001' LIMIT 1);

-- =========================================================
-- 3. PEMDA, OPD, JABATAN, PEGAWAI, USER
-- =========================================================

INSERT INTO pemda (
    kode_wilayah, nama, level_pemda, nama_kepala_daerah, jabatan_kepala_daerah,
    ibukota, alamat, website, email, telepon, is_aktif
)
SELECT
    '63.06',
    'Pemerintah Kabupaten Hulu Sungai Selatan',
    'KABUPATEN',
    'Bupati Simulasi',
    'Bupati Hulu Sungai Selatan',
    'Kandangan',
    'Jl. Pangeran Antasari No. 1 Kandangan',
    'https://hulusungaiselatankab.go.id',
    'pemkab@hulusungaiselatankab.go.id',
    '0517-000000',
    1
WHERE NOT EXISTS (
    SELECT 1 FROM pemda WHERE kode_wilayah = '63.06'
);

SET @pemda_id := (SELECT id FROM pemda WHERE kode_wilayah = '63.06' LIMIT 1);

INSERT INTO unit_organisasi (
    pemda_id, parent_id, kode_unit, nama, singkatan, jenis_unit, level_unit, urusan_id,
    alamat, email, telepon, is_aktif
)
SELECT @pemda_id, NULL, 'PEMDA', 'Pemerintah Kabupaten Hulu Sungai Selatan', 'Pemkab HSS', 'PEMDA', 'PEMDA', NULL,
       'Kandangan', 'pemkab@hulusungaiselatankab.go.id', '0517-000000', 1
WHERE NOT EXISTS (
    SELECT 1 FROM unit_organisasi WHERE pemda_id = @pemda_id AND kode_unit = 'PEMDA'
);

SET @unit_pemda_id := (SELECT id FROM unit_organisasi WHERE pemda_id = @pemda_id AND kode_unit = 'PEMDA' LIMIT 1);

INSERT INTO unit_organisasi (
    pemda_id, parent_id, kode_unit, nama, singkatan, jenis_unit, level_unit, urusan_id,
    alamat, email, telepon, is_aktif
)
SELECT @pemda_id, @unit_pemda_id, 'BAPPEDA', 'Badan Perencanaan Pembangunan Daerah', 'Bappeda', 'BADAN', 'OPD', NULL,
       'Kandangan', 'bappeda@hulusungaiselatankab.go.id', '0517-000001', 1
WHERE NOT EXISTS (
    SELECT 1 FROM unit_organisasi WHERE pemda_id = @pemda_id AND kode_unit = 'BAPPEDA'
);

INSERT INTO unit_organisasi (
    pemda_id, parent_id, kode_unit, nama, singkatan, jenis_unit, level_unit, urusan_id,
    alamat, email, telepon, is_aktif
)
SELECT @pemda_id, @unit_pemda_id, 'BAG_ORG', 'Bagian Organisasi Sekretariat Daerah', 'Bagian Organisasi', 'BAGIAN', 'OPD', NULL,
       'Kandangan', 'organisasi@hulusungaiselatankab.go.id', '0517-000002', 1
WHERE NOT EXISTS (
    SELECT 1 FROM unit_organisasi WHERE pemda_id = @pemda_id AND kode_unit = 'BAG_ORG'
);

INSERT INTO unit_organisasi (
    pemda_id, parent_id, kode_unit, nama, singkatan, jenis_unit, level_unit, urusan_id,
    alamat, email, telepon, is_aktif
)
SELECT @pemda_id, @unit_pemda_id, 'INSPEKTORAT', 'Inspektorat Daerah', 'Inspektorat', 'INSPEKTORAT', 'OPD', NULL,
       'Kandangan', 'inspektorat@hulusungaiselatankab.go.id', '0517-000003', 1
WHERE NOT EXISTS (
    SELECT 1 FROM unit_organisasi WHERE pemda_id = @pemda_id AND kode_unit = 'INSPEKTORAT'
);

INSERT INTO unit_organisasi (
    pemda_id, parent_id, kode_unit, nama, singkatan, jenis_unit, level_unit, urusan_id,
    alamat, email, telepon, is_aktif
)
SELECT @pemda_id, @unit_pemda_id, 'DISDIKBUD', 'Dinas Pendidikan dan Kebudayaan', 'Disdikbud', 'DINAS', 'OPD', @urusan_pendidikan_id,
       'Kandangan', 'disdikbud@hulusungaiselatankab.go.id', '0517-000004', 1
WHERE NOT EXISTS (
    SELECT 1 FROM unit_organisasi WHERE pemda_id = @pemda_id AND kode_unit = 'DISDIKBUD'
);

SET @unit_bappeda_id := (SELECT id FROM unit_organisasi WHERE pemda_id = @pemda_id AND kode_unit = 'BAPPEDA' LIMIT 1);
SET @unit_bagorg_id := (SELECT id FROM unit_organisasi WHERE pemda_id = @pemda_id AND kode_unit = 'BAG_ORG' LIMIT 1);
SET @unit_inspektorat_id := (SELECT id FROM unit_organisasi WHERE pemda_id = @pemda_id AND kode_unit = 'INSPEKTORAT' LIMIT 1);
SET @unit_disdikbud_id := (SELECT id FROM unit_organisasi WHERE pemda_id = @pemda_id AND kode_unit = 'DISDIKBUD' LIMIT 1);

INSERT INTO jabatan (unit_id, parent_id, nama, jenis_jabatan, eselon, kelas_jabatan, is_aktif)
SELECT @unit_disdikbud_id, NULL, 'Kepala Dinas Pendidikan dan Kebudayaan', 'KEPALA_OPD', 'II.b', NULL, 1
WHERE NOT EXISTS (
    SELECT 1 FROM jabatan WHERE unit_id = @unit_disdikbud_id AND nama = 'Kepala Dinas Pendidikan dan Kebudayaan'
);

INSERT INTO jabatan (unit_id, parent_id, nama, jenis_jabatan, eselon, kelas_jabatan, is_aktif)
SELECT @unit_bagorg_id, NULL, 'Kepala Bagian Organisasi', 'ADMINISTRATOR', 'III.a', NULL, 1
WHERE NOT EXISTS (
    SELECT 1 FROM jabatan WHERE unit_id = @unit_bagorg_id AND nama = 'Kepala Bagian Organisasi'
);

INSERT INTO jabatan (unit_id, parent_id, nama, jenis_jabatan, eselon, kelas_jabatan, is_aktif)
SELECT @unit_inspektorat_id, NULL, 'Inspektur Pembantu Wilayah I', 'ADMINISTRATOR', 'III.a', NULL, 1
WHERE NOT EXISTS (
    SELECT 1 FROM jabatan WHERE unit_id = @unit_inspektorat_id AND nama = 'Inspektur Pembantu Wilayah I'
);

SET @jab_kadis_disdikbud_id := (
    SELECT id FROM jabatan
    WHERE unit_id = @unit_disdikbud_id
      AND nama = 'Kepala Dinas Pendidikan dan Kebudayaan'
    LIMIT 1
);

SET @jab_bagorg_id := (
    SELECT id FROM jabatan
    WHERE unit_id = @unit_bagorg_id
      AND nama = 'Kepala Bagian Organisasi'
    LIMIT 1
);

SET @jab_irban_id := (
    SELECT id FROM jabatan
    WHERE unit_id = @unit_inspektorat_id
      AND nama = 'Inspektur Pembantu Wilayah I'
    LIMIT 1
);

INSERT INTO pegawai (
    pemda_id, unit_id, jabatan_id, nip, nik, nama, gelar_depan, gelar_belakang,
    email, telepon, status_pegawai, is_aktif
)
SELECT @pemda_id, @unit_disdikbud_id, @jab_kadis_disdikbud_id, '197001011990011001', NULL,
       'Drs. Ahmad Simulasi', NULL, 'M.Pd',
       'kadis.disdikbud@hulusungaiselatankab.go.id', '081100000001', 'PNS', 1
WHERE NOT EXISTS (
    SELECT 1 FROM pegawai WHERE nip = '197001011990011001'
);

INSERT INTO pegawai (
    pemda_id, unit_id, jabatan_id, nip, nik, nama, gelar_depan, gelar_belakang,
    email, telepon, status_pegawai, is_aktif
)
SELECT @pemda_id, @unit_bagorg_id, @jab_bagorg_id, '198001012005011001', NULL,
       'Siti Rahmah', NULL, 'S.Sos',
       'bagorg@hulusungaiselatankab.go.id', '081100000002', 'PNS', 1
WHERE NOT EXISTS (
    SELECT 1 FROM pegawai WHERE nip = '198001012005011001'
);

INSERT INTO pegawai (
    pemda_id, unit_id, jabatan_id, nip, nik, nama, gelar_depan, gelar_belakang,
    email, telepon, status_pegawai, is_aktif
)
SELECT @pemda_id, @unit_inspektorat_id, @jab_irban_id, '198101012006011001', NULL,
       'Muhammad Yusuf', NULL, 'S.E',
       'irban1@hulusungaiselatankab.go.id', '081100000003', 'PNS', 1
WHERE NOT EXISTS (
    SELECT 1 FROM pegawai WHERE nip = '198101012006011001'
);

SET @pegawai_kadis_id := (SELECT id FROM pegawai WHERE nip = '197001011990011001' LIMIT 1);
SET @pegawai_bagorg_id := (SELECT id FROM pegawai WHERE nip = '198001012005011001' LIMIT 1);
SET @pegawai_irban_id := (SELECT id FROM pegawai WHERE nip = '198101012006011001' LIMIT 1);

INSERT INTO app_role (kode, nama, deskripsi) VALUES
('SUPER_ADMIN', 'Super Admin', 'Pengelola seluruh sistem'),
('ADMIN_PEMDA', 'Admin Pemda', 'Pengelola data tingkat pemerintah daerah'),
('BAPPEDA', 'Bappeda', 'Koordinator perencanaan dan cascading kinerja daerah'),
('BAG_ORG', 'Bagian Organisasi', 'Koordinator SAKIP dan kualitas manajemen kinerja'),
('INSPEKTORAT', 'Inspektorat', 'Evaluator internal AKIP'),
('ADMIN_OPD', 'Admin OPD', 'Pengelola data SAKIP perangkat daerah'),
('KEPALA_OPD', 'Kepala OPD', 'Pemilik kinerja perangkat daerah'),
('OPERATOR', 'Operator', 'Input data kinerja dan bukti dukung'),
('PIMPINAN', 'Pimpinan', 'Pemantauan dashboard kinerja')
ON DUPLICATE KEY UPDATE nama = VALUES(nama), deskripsi = VALUES(deskripsi);

INSERT INTO app_permission (kode, nama) VALUES
('dashboard.view', 'Melihat Dashboard'),
('rpjmd.manage', 'Mengelola RPJMD'),
('renstra.manage', 'Mengelola Renstra'),
('renja.manage', 'Mengelola Renja'),
('pk.manage', 'Mengelola Perjanjian Kinerja'),
('realisasi.manage', 'Mengelola Realisasi Kinerja'),
('lkjip.manage', 'Mengelola LKJIP'),
('evaluasi.manage', 'Mengelola Evaluasi AKIP'),
('tindaklanjut.manage', 'Mengelola Tindak Lanjut'),
('dokumen.manage', 'Mengelola Dokumen')
ON DUPLICATE KEY UPDATE nama = VALUES(nama);

INSERT INTO app_user (
    pegawai_id, username, email, password_hash, nama, status
)
SELECT @pegawai_kadis_id, 'kadis.disdikbud', 'kadis.disdikbud@hulusungaiselatankab.go.id',
       '$2y$10$wHc6J2CbwJYkPZgOQXu7cOZ9O7b3bWL5Tr1km3JfFf2E4DsGzN4tC',
       'Drs. Ahmad Simulasi, M.Pd', 'AKTIF'
WHERE NOT EXISTS (
    SELECT 1 FROM app_user WHERE email = 'kadis.disdikbud@hulusungaiselatankab.go.id'
);

INSERT INTO app_user (
    pegawai_id, username, email, password_hash, nama, status
)
SELECT @pegawai_bagorg_id, 'bagorg', 'bagorg@hulusungaiselatankab.go.id',
       '$2y$10$wHc6J2CbwJYkPZgOQXu7cOZ9O7b3bWL5Tr1km3JfFf2E4DsGzN4tC',
       'Siti Rahmah, S.Sos', 'AKTIF'
WHERE NOT EXISTS (
    SELECT 1 FROM app_user WHERE email = 'bagorg@hulusungaiselatankab.go.id'
);

INSERT INTO app_user (
    pegawai_id, username, email, password_hash, nama, status
)
SELECT @pegawai_irban_id, 'irban1', 'irban1@hulusungaiselatankab.go.id',
       '$2y$10$wHc6J2CbwJYkPZgOQXu7cOZ9O7b3bWL5Tr1km3JfFf2E4DsGzN4tC',
       'Muhammad Yusuf, S.E', 'AKTIF'
WHERE NOT EXISTS (
    SELECT 1 FROM app_user WHERE email = 'irban1@hulusungaiselatankab.go.id'
);

SET @user_kadis_id := (SELECT id FROM app_user WHERE email = 'kadis.disdikbud@hulusungaiselatankab.go.id' LIMIT 1);
SET @user_bagorg_id := (SELECT id FROM app_user WHERE email = 'bagorg@hulusungaiselatankab.go.id' LIMIT 1);
SET @user_irban_id := (SELECT id FROM app_user WHERE email = 'irban1@hulusungaiselatankab.go.id' LIMIT 1);

SET @role_kepala_opd_id := (SELECT id FROM app_role WHERE kode = 'KEPALA_OPD' LIMIT 1);
SET @role_bagorg_id := (SELECT id FROM app_role WHERE kode = 'BAG_ORG' LIMIT 1);
SET @role_inspektorat_id := (SELECT id FROM app_role WHERE kode = 'INSPEKTORAT' LIMIT 1);

INSERT IGNORE INTO app_user_role (user_id, role_id, unit_id) VALUES
(@user_kadis_id, @role_kepala_opd_id, @unit_disdikbud_id),
(@user_bagorg_id, @role_bagorg_id, @unit_bagorg_id),
(@user_irban_id, @role_inspektorat_id, @unit_inspektorat_id);

-- =========================================================
-- 4. DOKUMEN PERENCANAAN TAHUNAN
-- =========================================================

SET @jenis_rpjmd_id := (SELECT id FROM ref_dokumen_jenis WHERE kode = 'RPJMD' LIMIT 1);
SET @jenis_rkpd_id := (SELECT id FROM ref_dokumen_jenis WHERE kode = 'RKPD' LIMIT 1);
SET @jenis_renstra_id := (SELECT id FROM ref_dokumen_jenis WHERE kode = 'RENSTRA' LIMIT 1);
SET @jenis_renja_id := (SELECT id FROM ref_dokumen_jenis WHERE kode = 'RENJA' LIMIT 1);
SET @jenis_pk_id := (SELECT id FROM ref_dokumen_jenis WHERE kode = 'PK' LIMIT 1);
SET @jenis_lkjip_opd_id := (SELECT id FROM ref_dokumen_jenis WHERE kode = 'LKJIP_OPD' LIMIT 1);
SET @jenis_lkjip_pemda_id := (SELECT id FROM ref_dokumen_jenis WHERE kode = 'LKJIP_PEMDA' LIMIT 1);
SET @jenis_bukti_id := (SELECT id FROM ref_dokumen_jenis WHERE kode = 'BUKTI_DUKUNG' LIMIT 1);

INSERT INTO dokumen (
    pemda_id, unit_id, jenis_dokumen_id, tahun, periode_awal, periode_akhir,
    nomor_dokumen, judul, ringkasan, status, tanggal_dokumen, tanggal_penetapan, created_by
)
SELECT
@pemda_id, @unit_pemda_id, @jenis_rpjmd_id, 2025, 2025, 2029,
 'RPJMD-SIM-2025-2029', 'RPJMD Kabupaten Hulu Sungai Selatan Tahun 2025-2029',
 'Dokumen simulasi RPJMD sebagai dasar cascading SAKIP tahun 2026.', 'DITETAPKAN',
 '2025-08-01', '2025-08-15', @user_bagorg_id
WHERE NOT EXISTS (SELECT 1 FROM dokumen WHERE nomor_dokumen = 'RPJMD-SIM-2025-2029');

SET @dok_rpjmd_id := (SELECT id FROM dokumen WHERE nomor_dokumen = 'RPJMD-SIM-2025-2029' LIMIT 1);

INSERT INTO rpjmd_dokumen (
    pemda_id, dokumen_id, tahun_awal, tahun_akhir, visi, misi_ringkas, status
)
SELECT
    @pemda_id,
    @dok_rpjmd_id,
    2025,
    2029,
    'Terwujudnya Hulu Sungai Selatan yang maju, sejahtera, religius, dan berdaya saing.',
    'Meningkatkan kualitas SDM, pelayanan publik, tata kelola pemerintahan, dan pembangunan ekonomi daerah.',
    'PERDA'
WHERE NOT EXISTS (SELECT 1 FROM rpjmd_dokumen WHERE dokumen_id = @dok_rpjmd_id);

SET @rpjmd_id := (SELECT id FROM rpjmd_dokumen WHERE dokumen_id = @dok_rpjmd_id LIMIT 1);

INSERT INTO dokumen (
    pemda_id, unit_id, jenis_dokumen_id, tahun, periode_awal, periode_akhir,
    nomor_dokumen, judul, ringkasan, status, tanggal_dokumen, tanggal_penetapan, created_by
)
SELECT
@pemda_id, @unit_pemda_id, @jenis_rkpd_id, @tahun, @tahun, @tahun,
 'RKPD-SIM-2026', 'RKPD Kabupaten Hulu Sungai Selatan Tahun 2026',
 'Dokumen simulasi RKPD tahun 2026.', 'DITETAPKAN',
 '2025-06-30', '2025-07-15', @user_bagorg_id
WHERE NOT EXISTS (SELECT 1 FROM dokumen WHERE nomor_dokumen = 'RKPD-SIM-2026');

SET @dok_rkpd_id := (SELECT id FROM dokumen WHERE nomor_dokumen = 'RKPD-SIM-2026' LIMIT 1);

INSERT INTO rkpd_dokumen (
    pemda_id, dokumen_id, tahun, tema_pembangunan, prioritas_daerah, status
)
SELECT
    @pemda_id,
    @dok_rkpd_id,
    @tahun,
    'Penguatan kualitas sumber daya manusia dan pelayanan publik berbasis data.',
    'Peningkatan mutu pendidikan dasar, transformasi digital layanan publik, dan penguatan akuntabilitas kinerja.',
    'PERKADA'
WHERE NOT EXISTS (SELECT 1 FROM rkpd_dokumen WHERE dokumen_id = @dok_rkpd_id);

SET @rkpd_id := (SELECT id FROM rkpd_dokumen WHERE dokumen_id = @dok_rkpd_id LIMIT 1);

INSERT INTO dokumen (
    pemda_id, unit_id, jenis_dokumen_id, tahun, periode_awal, periode_akhir,
    nomor_dokumen, judul, ringkasan, status, tanggal_dokumen, tanggal_penetapan, created_by
)
SELECT
@pemda_id, @unit_disdikbud_id, @jenis_renstra_id, 2025, 2025, 2029,
 'RENSTRA-DISDIKBUD-SIM-2025-2029', 'Renstra Dinas Pendidikan dan Kebudayaan Tahun 2025-2029',
 'Dokumen simulasi Renstra Disdikbud.', 'DITETAPKAN',
 '2025-09-01', '2025-09-15', @user_kadis_id
WHERE NOT EXISTS (SELECT 1 FROM dokumen WHERE nomor_dokumen = 'RENSTRA-DISDIKBUD-SIM-2025-2029');

SET @dok_renstra_id := (SELECT id FROM dokumen WHERE nomor_dokumen = 'RENSTRA-DISDIKBUD-SIM-2025-2029' LIMIT 1);

INSERT INTO renstra_dokumen (
    pemda_id, unit_id, dokumen_id, rpjmd_id, tahun_awal, tahun_akhir, isu_strategis, status
)
SELECT
    @pemda_id,
    @unit_disdikbud_id,
    @dok_renstra_id,
    @rpjmd_id,
    2025,
    2029,
    'Pemerataan akses pendidikan, peningkatan mutu pembelajaran, transformasi digital sekolah, dan peningkatan akuntabilitas layanan pendidikan.',
    'DITETAPKAN'
WHERE NOT EXISTS (SELECT 1 FROM renstra_dokumen WHERE dokumen_id = @dok_renstra_id);

SET @renstra_id := (SELECT id FROM renstra_dokumen WHERE dokumen_id = @dok_renstra_id LIMIT 1);

INSERT INTO dokumen (
    pemda_id, unit_id, jenis_dokumen_id, tahun, periode_awal, periode_akhir,
    nomor_dokumen, judul, ringkasan, status, tanggal_dokumen, tanggal_penetapan, created_by
)
SELECT
@pemda_id, @unit_disdikbud_id, @jenis_renja_id, @tahun, @tahun, @tahun,
 'RENJA-DISDIKBUD-SIM-2026', 'Renja Dinas Pendidikan dan Kebudayaan Tahun 2026',
 'Dokumen simulasi Renja Disdikbud tahun 2026.', 'DITETAPKAN',
 '2025-07-20', '2025-08-05', @user_kadis_id
WHERE NOT EXISTS (SELECT 1 FROM dokumen WHERE nomor_dokumen = 'RENJA-DISDIKBUD-SIM-2026');

SET @dok_renja_id := (SELECT id FROM dokumen WHERE nomor_dokumen = 'RENJA-DISDIKBUD-SIM-2026' LIMIT 1);

INSERT INTO renja_dokumen (
    pemda_id, unit_id, dokumen_id, renstra_id, rkpd_id, tahun, status
)
SELECT
    @pemda_id,
    @unit_disdikbud_id,
    @dok_renja_id,
    @renstra_id,
    @rkpd_id,
    @tahun,
    'DITETAPKAN'
WHERE NOT EXISTS (SELECT 1 FROM renja_dokumen WHERE dokumen_id = @dok_renja_id);

SET @renja_id := (SELECT id FROM renja_dokumen WHERE dokumen_id = @dok_renja_id LIMIT 1);

-- =========================================================
-- 5. POHON KINERJA DAN CASCADING
-- =========================================================

INSERT INTO sakip_kinerja_node (
    pemda_id, unit_id, parent_id, kode, jenis_node, uraian, level_kinerja,
    tahun_awal, tahun_akhir, rpjmd_id, renstra_id, rkpd_id, renja_id,
    ref_program_id, ref_kegiatan_id, ref_sub_kegiatan_id,
    urutan, is_prioritas, status, created_by
)
SELECT
@pemda_id, @unit_pemda_id, NULL, 'MISI-1', 'MISI',
 'Meningkatkan kualitas sumber daya manusia yang berdaya saing.',
 'PEMDA', 2025, 2029, @rpjmd_id, NULL, NULL, NULL, NULL, NULL, NULL, 1, 1, 'AKTIF', @user_bagorg_id
WHERE NOT EXISTS (SELECT 1 FROM sakip_kinerja_node WHERE pemda_id = @pemda_id AND kode = 'MISI-1');

SET @node_misi_id := (SELECT id FROM sakip_kinerja_node WHERE pemda_id = @pemda_id AND kode = 'MISI-1' LIMIT 1);

INSERT INTO sakip_kinerja_node (
    pemda_id, unit_id, parent_id, kode, jenis_node, uraian, level_kinerja,
    tahun_awal, tahun_akhir, rpjmd_id, renstra_id, rkpd_id, renja_id,
    urutan, is_prioritas, status, created_by
)
SELECT
@pemda_id, @unit_pemda_id, @node_misi_id, 'TD-1', 'TUJUAN_DAERAH',
 'Meningkatnya kualitas dan daya saing pendidikan masyarakat.',
 'PEMDA', 2025, 2029, @rpjmd_id, NULL, NULL, NULL, 1, 1, 'AKTIF', @user_bagorg_id
WHERE NOT EXISTS (SELECT 1 FROM sakip_kinerja_node WHERE pemda_id = @pemda_id AND kode = 'TD-1');

SET @node_tujuan_daerah_id := (SELECT id FROM sakip_kinerja_node WHERE pemda_id = @pemda_id AND kode = 'TD-1' LIMIT 1);

INSERT INTO sakip_kinerja_node (
    pemda_id, unit_id, parent_id, kode, jenis_node, uraian, level_kinerja,
    tahun_awal, tahun_akhir, rpjmd_id, renstra_id, rkpd_id, renja_id,
    urutan, is_prioritas, status, created_by
)
SELECT
@pemda_id, @unit_pemda_id, @node_tujuan_daerah_id, 'SD-1', 'SASARAN_DAERAH',
 'Meningkatnya akses dan mutu layanan pendidikan dasar.',
 'PEMDA', 2025, 2029, @rpjmd_id, NULL, @rkpd_id, NULL, 1, 1, 'AKTIF', @user_bagorg_id
WHERE NOT EXISTS (SELECT 1 FROM sakip_kinerja_node WHERE pemda_id = @pemda_id AND kode = 'SD-1');

SET @node_sasaran_daerah_id := (SELECT id FROM sakip_kinerja_node WHERE pemda_id = @pemda_id AND kode = 'SD-1' LIMIT 1);

INSERT INTO sakip_kinerja_node (
    pemda_id, unit_id, parent_id, kode, jenis_node, uraian, level_kinerja,
    tahun_awal, tahun_akhir, rpjmd_id, renstra_id, rkpd_id, renja_id,
    urutan, is_prioritas, status, created_by
)
SELECT
@pemda_id, @unit_disdikbud_id, @node_sasaran_daerah_id, 'TO-1', 'TUJUAN_OPD',
 'Meningkatkan layanan pendidikan dasar yang merata dan bermutu.',
 'OPD', 2025, 2029, @rpjmd_id, @renstra_id, NULL, NULL, 1, 1, 'AKTIF', @user_kadis_id
WHERE NOT EXISTS (SELECT 1 FROM sakip_kinerja_node WHERE pemda_id = @pemda_id AND kode = 'TO-1');

SET @node_tujuan_opd_id := (SELECT id FROM sakip_kinerja_node WHERE pemda_id = @pemda_id AND kode = 'TO-1' LIMIT 1);

INSERT INTO sakip_kinerja_node (
    pemda_id, unit_id, parent_id, kode, jenis_node, uraian, level_kinerja,
    tahun_awal, tahun_akhir, rpjmd_id, renstra_id, rkpd_id, renja_id,
    urutan, is_prioritas, status, created_by
)
SELECT
@pemda_id, @unit_disdikbud_id, @node_tujuan_opd_id, 'SO-1', 'SASARAN_OPD',
 'Meningkatnya mutu pembelajaran dan pemerataan akses pendidikan SD dan SMP.',
 'OPD', 2025, 2029, @rpjmd_id, @renstra_id, @rkpd_id, @renja_id, 1, 1, 'AKTIF', @user_kadis_id
WHERE NOT EXISTS (SELECT 1 FROM sakip_kinerja_node WHERE pemda_id = @pemda_id AND kode = 'SO-1');

SET @node_sasaran_opd_id := (SELECT id FROM sakip_kinerja_node WHERE pemda_id = @pemda_id AND kode = 'SO-1' LIMIT 1);

INSERT INTO sakip_kinerja_node (
    pemda_id, unit_id, parent_id, kode, jenis_node, uraian, level_kinerja,
    tahun_awal, tahun_akhir, rpjmd_id, renstra_id, rkpd_id, renja_id,
    ref_program_id, urutan, is_prioritas, status, created_by
)
SELECT
@pemda_id, @unit_disdikbud_id, @node_sasaran_opd_id, 'PRG-1.01.02', 'PROGRAM',
 'Program Pengelolaan Pendidikan.',
 'OPD', 2026, 2026, @rpjmd_id, @renstra_id, @rkpd_id, @renja_id,
 @program_pendidikan_id, 1, 1, 'AKTIF', @user_kadis_id
WHERE NOT EXISTS (SELECT 1 FROM sakip_kinerja_node WHERE pemda_id = @pemda_id AND kode = 'PRG-1.01.02');

SET @node_program_id := (SELECT id FROM sakip_kinerja_node WHERE pemda_id = @pemda_id AND kode = 'PRG-1.01.02' LIMIT 1);

INSERT INTO sakip_kinerja_node (
    pemda_id, unit_id, parent_id, kode, jenis_node, uraian, level_kinerja,
    tahun_awal, tahun_akhir, rpjmd_id, renstra_id, rkpd_id, renja_id,
    ref_program_id, ref_kegiatan_id, urutan, is_prioritas, status, created_by
)
SELECT
@pemda_id, @unit_disdikbud_id, @node_program_id, 'KEG-SD', 'KEGIATAN',
 'Pengelolaan Pendidikan Sekolah Dasar.',
 'OPD', 2026, 2026, @rpjmd_id, @renstra_id, @rkpd_id, @renja_id,
 @program_pendidikan_id, @kegiatan_sd_id, 1, 1, 'AKTIF', @user_kadis_id
WHERE NOT EXISTS (SELECT 1 FROM sakip_kinerja_node WHERE pemda_id = @pemda_id AND kode = 'KEG-SD');

SET @node_kegiatan_sd_id := (SELECT id FROM sakip_kinerja_node WHERE pemda_id = @pemda_id AND kode = 'KEG-SD' LIMIT 1);

INSERT INTO sakip_kinerja_node (
    pemda_id, unit_id, parent_id, kode, jenis_node, uraian, level_kinerja,
    tahun_awal, tahun_akhir, rpjmd_id, renstra_id, rkpd_id, renja_id,
    ref_program_id, ref_kegiatan_id, urutan, is_prioritas, status, created_by
)
SELECT
@pemda_id, @unit_disdikbud_id, @node_program_id, 'KEG-SMP', 'KEGIATAN',
 'Pengelolaan Pendidikan Sekolah Menengah Pertama.',
 'OPD', 2026, 2026, @rpjmd_id, @renstra_id, @rkpd_id, @renja_id,
 @program_pendidikan_id, @kegiatan_smp_id, 2, 1, 'AKTIF', @user_kadis_id
WHERE NOT EXISTS (SELECT 1 FROM sakip_kinerja_node WHERE pemda_id = @pemda_id AND kode = 'KEG-SMP');

SET @node_kegiatan_smp_id := (SELECT id FROM sakip_kinerja_node WHERE pemda_id = @pemda_id AND kode = 'KEG-SMP' LIMIT 1);

INSERT INTO sakip_kinerja_node (
    pemda_id, unit_id, parent_id, kode, jenis_node, uraian, level_kinerja,
    tahun_awal, tahun_akhir, rpjmd_id, renstra_id, rkpd_id, renja_id,
    ref_program_id, ref_kegiatan_id, ref_sub_kegiatan_id,
    urutan, is_prioritas, status, created_by
)
SELECT
@pemda_id, @unit_disdikbud_id, @node_kegiatan_sd_id, 'SUB-SD-01', 'SUB_KEGIATAN',
 'Penyediaan layanan pendidikan Sekolah Dasar.',
 'OPD', 2026, 2026, @rpjmd_id, @renstra_id, @rkpd_id, @renja_id,
 @program_pendidikan_id, @kegiatan_sd_id, @sub_sd_id,
 1, 1, 'AKTIF', @user_kadis_id
WHERE NOT EXISTS (SELECT 1 FROM sakip_kinerja_node WHERE pemda_id = @pemda_id AND kode = 'SUB-SD-01');

SET @node_sub_sd_id := (SELECT id FROM sakip_kinerja_node WHERE pemda_id = @pemda_id AND kode = 'SUB-SD-01' LIMIT 1);

INSERT INTO sakip_kinerja_node (
    pemda_id, unit_id, parent_id, kode, jenis_node, uraian, level_kinerja,
    tahun_awal, tahun_akhir, rpjmd_id, renstra_id, rkpd_id, renja_id,
    ref_program_id, ref_kegiatan_id, ref_sub_kegiatan_id,
    urutan, is_prioritas, status, created_by
)
SELECT
@pemda_id, @unit_disdikbud_id, @node_kegiatan_smp_id, 'SUB-SMP-01', 'SUB_KEGIATAN',
 'Penyediaan layanan pendidikan Sekolah Menengah Pertama.',
 'OPD', 2026, 2026, @rpjmd_id, @renstra_id, @rkpd_id, @renja_id,
 @program_pendidikan_id, @kegiatan_smp_id, @sub_smp_id,
 1, 1, 'AKTIF', @user_kadis_id
WHERE NOT EXISTS (SELECT 1 FROM sakip_kinerja_node WHERE pemda_id = @pemda_id AND kode = 'SUB-SMP-01');

SET @node_sub_smp_id := (SELECT id FROM sakip_kinerja_node WHERE pemda_id = @pemda_id AND kode = 'SUB-SMP-01' LIMIT 1);

INSERT INTO sakip_cascading_relasi (
    parent_node_id, child_node_id, jenis_relasi, bobot_kontribusi, logika_kontribusi
)
VALUES
(@node_misi_id, @node_tujuan_daerah_id, 'TURUNAN_LANGSUNG', 100.00, 'Tujuan daerah menjadi penjabaran langsung misi peningkatan kualitas SDM.'),
(@node_tujuan_daerah_id, @node_sasaran_daerah_id, 'TURUNAN_LANGSUNG', 100.00, 'Akses dan mutu pendidikan dasar menjadi faktor utama kualitas pendidikan masyarakat.'),
(@node_sasaran_daerah_id, @node_tujuan_opd_id, 'KONTRIBUSI', 100.00, 'Disdikbud menjadi perangkat daerah utama untuk sasaran pendidikan dasar.'),
(@node_tujuan_opd_id, @node_sasaran_opd_id, 'TURUNAN_LANGSUNG', 100.00, 'Sasaran OPD memecah tujuan layanan pendidikan merata dan bermutu.'),
(@node_sasaran_opd_id, @node_program_id, 'TURUNAN_LANGSUNG', 100.00, 'Program Pengelolaan Pendidikan menjadi instrumen utama sasaran OPD.'),
(@node_program_id, @node_kegiatan_sd_id, 'TURUNAN_LANGSUNG', 50.00, 'Kegiatan SD mendukung program pendidikan.'),
(@node_program_id, @node_kegiatan_smp_id, 'TURUNAN_LANGSUNG', 50.00, 'Kegiatan SMP mendukung program pendidikan.'),
(@node_kegiatan_sd_id, @node_sub_sd_id, 'TURUNAN_LANGSUNG', 100.00, 'Sub kegiatan SD menjadi keluaran teknis kegiatan SD.'),
(@node_kegiatan_smp_id, @node_sub_smp_id, 'TURUNAN_LANGSUNG', 100.00, 'Sub kegiatan SMP menjadi keluaran teknis kegiatan SMP.')
ON DUPLICATE KEY UPDATE
    bobot_kontribusi = VALUES(bobot_kontribusi),
    logika_kontribusi = VALUES(logika_kontribusi);

-- =========================================================
-- 6. INDIKATOR, TARGET, REALISASI, CAPAIAN
-- =========================================================

SET @satuan_persen_id := (SELECT id FROM ref_satuan WHERE kode = 'PERSEN' LIMIT 1);
SET @satuan_indeks_id := (SELECT id FROM ref_satuan WHERE kode = 'INDEKS' LIMIT 1);
SET @satuan_sekolah_id := (SELECT id FROM ref_satuan WHERE kode = 'SEKOLAH' LIMIT 1);

INSERT INTO sakip_indikator (
    node_id, kode, nama, definisi_operasional, formula, satuan_id, jenis_indikator,
    arah_capaian, sumber_data, metode_pengukuran, frekuensi_pengukuran,
    penanggung_jawab_unit_id, penanggung_jawab_pegawai_id,
    is_iku, is_pk, is_publikasi, status
)
SELECT
@node_sasaran_daerah_id, 'IKD-01', 'Indeks Layanan Pendidikan Dasar',
 'Indeks komposit yang menggambarkan akses, mutu, dan tata kelola layanan pendidikan dasar.',
 '(akses * 0.4) + (mutu * 0.4) + (tata_kelola * 0.2)', @satuan_indeks_id, 'IKD',
 'MAKSIMAL', 'Dapodik, rapor pendidikan, dan laporan OPD', 'Kompilasi data tahunan', 'TAHUNAN',
 @unit_bappeda_id, NULL, 1, 0, 1, 'AKTIF'
WHERE NOT EXISTS (SELECT 1 FROM sakip_indikator WHERE node_id = @node_sasaran_daerah_id AND kode = 'IKD-01');

SET @indikator_daerah_id := (SELECT id FROM sakip_indikator WHERE node_id = @node_sasaran_daerah_id AND kode = 'IKD-01' LIMIT 1);

INSERT INTO sakip_indikator (
    node_id, kode, nama, definisi_operasional, formula, satuan_id, jenis_indikator,
    arah_capaian, sumber_data, metode_pengukuran, frekuensi_pengukuran,
    penanggung_jawab_unit_id, penanggung_jawab_pegawai_id,
    is_iku, is_pk, is_publikasi, status
)
SELECT
@node_sasaran_opd_id, 'IKU-DISDIKBUD-01', 'Persentase satuan pendidikan dasar berkinerja baik',
 'Persentase SD dan SMP yang memenuhi kriteria kinerja layanan pendidikan minimal baik.',
 '(jumlah sekolah berkinerja baik / total sekolah) * 100', @satuan_persen_id, 'IKU',
 'MAKSIMAL', 'Rapor pendidikan, Dapodik, dan hasil monitoring sekolah', 'Rekapitulasi tahunan', 'TRIWULANAN',
 @unit_disdikbud_id, @pegawai_kadis_id, 1, 1, 1, 'AKTIF'
WHERE NOT EXISTS (SELECT 1 FROM sakip_indikator WHERE node_id = @node_sasaran_opd_id AND kode = 'IKU-DISDIKBUD-01');

SET @indikator_opd_id := (SELECT id FROM sakip_indikator WHERE node_id = @node_sasaran_opd_id AND kode = 'IKU-DISDIKBUD-01' LIMIT 1);

INSERT INTO sakip_indikator (
    node_id, kode, nama, definisi_operasional, formula, satuan_id, jenis_indikator,
    arah_capaian, sumber_data, metode_pengukuran, frekuensi_pengukuran,
    penanggung_jawab_unit_id, penanggung_jawab_pegawai_id,
    is_iku, is_pk, is_publikasi, status
)
SELECT
@node_sub_sd_id, 'OUT-SD-01', 'Jumlah SD yang mendapat layanan peningkatan mutu',
 'Jumlah sekolah dasar yang mendapatkan intervensi peningkatan mutu pembelajaran.',
 'Jumlah SD penerima layanan', @satuan_sekolah_id, 'OUTPUT',
 'MAKSIMAL', 'Laporan bidang SD', 'Rekapitulasi bulanan dan tahunan', 'TRIWULANAN',
 @unit_disdikbud_id, @pegawai_kadis_id, 0, 1, 0, 'AKTIF'
WHERE NOT EXISTS (SELECT 1 FROM sakip_indikator WHERE node_id = @node_sub_sd_id AND kode = 'OUT-SD-01');

SET @indikator_sd_id := (SELECT id FROM sakip_indikator WHERE node_id = @node_sub_sd_id AND kode = 'OUT-SD-01' LIMIT 1);

INSERT INTO sakip_indikator (
    node_id, kode, nama, definisi_operasional, formula, satuan_id, jenis_indikator,
    arah_capaian, sumber_data, metode_pengukuran, frekuensi_pengukuran,
    penanggung_jawab_unit_id, penanggung_jawab_pegawai_id,
    is_iku, is_pk, is_publikasi, status
)
SELECT
@node_sub_smp_id, 'OUT-SMP-01', 'Jumlah SMP yang mendapat layanan peningkatan mutu',
 'Jumlah sekolah menengah pertama yang mendapatkan intervensi peningkatan mutu pembelajaran.',
 'Jumlah SMP penerima layanan', @satuan_sekolah_id, 'OUTPUT',
 'MAKSIMAL', 'Laporan bidang SMP', 'Rekapitulasi bulanan dan tahunan', 'TRIWULANAN',
 @unit_disdikbud_id, @pegawai_kadis_id, 0, 1, 0, 'AKTIF'
WHERE NOT EXISTS (SELECT 1 FROM sakip_indikator WHERE node_id = @node_sub_smp_id AND kode = 'OUT-SMP-01');

SET @indikator_smp_id := (SELECT id FROM sakip_indikator WHERE node_id = @node_sub_smp_id AND kode = 'OUT-SMP-01' LIMIT 1);

INSERT INTO sakip_target (
    indikator_id, tahun, periode, target_angka, target_teks, target_min, target_max,
    baseline, pagu_indikatif, catatan
)
VALUES
(@indikator_daerah_id, @tahun, 'TAHUNAN', 78.00, NULL, NULL, NULL, 74.00, 24500000000.00, 'Target indeks layanan pendidikan dasar tahun 2026.'),
(@indikator_opd_id, @tahun, 'TAHUNAN', 72.00, NULL, NULL, NULL, 65.00, 24500000000.00, 'Target IKU Disdikbud tahun 2026.'),
(@indikator_sd_id, @tahun, 'TAHUNAN', 180.00, NULL, NULL, NULL, 165.00, 16000000000.00, 'Target output layanan SD tahun 2026.'),
(@indikator_smp_id, @tahun, 'TAHUNAN', 45.00, NULL, NULL, NULL, 40.00, 8500000000.00, 'Target output layanan SMP tahun 2026.')
ON DUPLICATE KEY UPDATE
    target_angka = VALUES(target_angka),
    target_teks = VALUES(target_teks),
    target_min = VALUES(target_min),
    target_max = VALUES(target_max),
    baseline = VALUES(baseline),
    pagu_indikatif = VALUES(pagu_indikatif),
    catatan = VALUES(catatan);

SET @target_daerah_id := (SELECT id FROM sakip_target WHERE indikator_id = @indikator_daerah_id AND tahun = @tahun AND periode = 'TAHUNAN' LIMIT 1);
SET @target_opd_id := (SELECT id FROM sakip_target WHERE indikator_id = @indikator_opd_id AND tahun = @tahun AND periode = 'TAHUNAN' LIMIT 1);
SET @target_sd_id := (SELECT id FROM sakip_target WHERE indikator_id = @indikator_sd_id AND tahun = @tahun AND periode = 'TAHUNAN' LIMIT 1);
SET @target_smp_id := (SELECT id FROM sakip_target WHERE indikator_id = @indikator_smp_id AND tahun = @tahun AND periode = 'TAHUNAN' LIMIT 1);

INSERT INTO sakip_realisasi (
    indikator_id, tahun, periode, realisasi_angka, realisasi_teks, tanggal_input,
    sumber_data, kendala, upaya_perbaikan, status_validasi,
    validator_user_id, validated_at
)
VALUES
(@indikator_daerah_id, @tahun, 'TAHUNAN', 76.50, NULL, '2026-12-31',
 'Dapodik, rapor pendidikan, laporan Disdikbud', 'Sebagian satuan pendidikan belum mencapai standar mutu minimal.', 'Penguatan pendampingan sekolah dan integrasi data mutu.', 'VALID',
 @user_bagorg_id, '2027-01-10 10:00:00'),
(@indikator_opd_id, @tahun, 'TAHUNAN', 70.00, NULL, '2026-12-31',
 'Rapor pendidikan dan monitoring sekolah', 'Sebagian sekolah membutuhkan pendampingan pembelajaran dan manajemen data.', 'Pendampingan sekolah berbasis data rapor pendidikan.', 'VALID',
 @user_bagorg_id, '2027-01-10 10:10:00'),
(@indikator_sd_id, @tahun, 'TAHUNAN', 176.00, NULL, '2026-12-31',
 'Laporan bidang SD', 'Jadwal pendampingan beberapa sekolah mundur.', 'Penjadwalan ulang dan pendampingan daring.', 'VALID',
 @user_bagorg_id, '2027-01-10 10:20:00'),
(@indikator_smp_id, @tahun, 'TAHUNAN', 44.00, NULL, '2026-12-31',
 'Laporan bidang SMP', 'Sebagian sekolah terlambat melengkapi dokumen mutu.', 'Klinik pengisian data dan verifikasi dokumen.', 'VALID',
 @user_bagorg_id, '2027-01-10 10:30:00')
ON DUPLICATE KEY UPDATE
    realisasi_angka = VALUES(realisasi_angka),
    realisasi_teks = VALUES(realisasi_teks),
    tanggal_input = VALUES(tanggal_input),
    sumber_data = VALUES(sumber_data),
    kendala = VALUES(kendala),
    upaya_perbaikan = VALUES(upaya_perbaikan),
    status_validasi = VALUES(status_validasi),
    validator_user_id = VALUES(validator_user_id),
    validated_at = VALUES(validated_at);

SET @realisasi_daerah_id := (SELECT id FROM sakip_realisasi WHERE indikator_id = @indikator_daerah_id AND tahun = @tahun AND periode = 'TAHUNAN' LIMIT 1);
SET @realisasi_opd_id := (SELECT id FROM sakip_realisasi WHERE indikator_id = @indikator_opd_id AND tahun = @tahun AND periode = 'TAHUNAN' LIMIT 1);
SET @realisasi_sd_id := (SELECT id FROM sakip_realisasi WHERE indikator_id = @indikator_sd_id AND tahun = @tahun AND periode = 'TAHUNAN' LIMIT 1);
SET @realisasi_smp_id := (SELECT id FROM sakip_realisasi WHERE indikator_id = @indikator_smp_id AND tahun = @tahun AND periode = 'TAHUNAN' LIMIT 1);

INSERT INTO sakip_capaian (
    indikator_id, target_id, realisasi_id, capaian_persen, predikat,
    analisis_capaian, analisis_efisiensi, faktor_pendorong, faktor_penghambat, rekomendasi_perbaikan
)
VALUES
(@indikator_daerah_id, @target_daerah_id, @realisasi_daerah_id, 98.08, 'Baik',
 'Capaian indeks layanan pendidikan dasar mendekati target tahunan.',
 'Pagu pendidikan digunakan untuk intervensi sekolah prioritas.',
 'Dukungan data Dapodik dan rapor pendidikan semakin baik.',
 'Kualitas data sekolah belum merata.',
 'Perkuat validasi data dan pendampingan sekolah berbasis kebutuhan.'),
(@indikator_opd_id, @target_opd_id, @realisasi_opd_id, 97.22, 'Baik',
 'Capaian IKU Disdikbud mendekati target, tetapi belum mencapai 100 persen.',
 'Efisiensi dilakukan melalui pemetaan sekolah prioritas.',
 'Koordinasi bidang SD dan SMP berjalan baik.',
 'Sebagian sekolah belum siap menerapkan perbaikan mutu berbasis data.',
 'Perkuat monitoring triwulanan dan dashboard sekolah.'),
(@indikator_sd_id, @target_sd_id, @realisasi_sd_id, 97.78, 'Baik',
 'Sebagian besar SD target sudah mendapat layanan peningkatan mutu.',
 'Pelaksanaan kegiatan SD berjalan cukup efisien.',
 'Data sekolah tersedia dan koordinasi pengawas baik.',
 'Sebagian wilayah sulit dijangkau pada periode tertentu.',
 'Gunakan pola pendampingan hybrid.'),
(@indikator_smp_id, @target_smp_id, @realisasi_smp_id, 97.78, 'Baik',
 'Sebagian besar SMP target sudah mendapat layanan peningkatan mutu.',
 'Anggaran diarahkan ke sekolah yang membutuhkan intervensi.',
 'Komitmen kepala sekolah baik.',
 'Kelengkapan dokumen mutu belum merata.',
 'Lakukan klinik mutu dan verifikasi dokumen lebih awal.')
ON DUPLICATE KEY UPDATE
    capaian_persen = VALUES(capaian_persen),
    predikat = VALUES(predikat),
    analisis_capaian = VALUES(analisis_capaian),
    analisis_efisiensi = VALUES(analisis_efisiensi),
    faktor_pendorong = VALUES(faktor_pendorong),
    faktor_penghambat = VALUES(faktor_penghambat),
    rekomendasi_perbaikan = VALUES(rekomendasi_perbaikan);

-- =========================================================
-- 7. ANGGARAN DAN REALISASI ANGGARAN
-- =========================================================

INSERT INTO anggaran_pagu (
    pemda_id, unit_id, node_id, tahun, jenis_pagu,
    belanja_operasi, belanja_modal, belanja_tidak_terduga, belanja_transfer,
    total_pagu, sumber_dana, catatan
)
SELECT
@pemda_id, @unit_disdikbud_id, @node_program_id, @tahun, 'DPA',
 18500000000.00, 6000000000.00, 0.00, 0.00, 24500000000.00,
 'DAU, DAK, PAD', 'Pagu simulasi Program Pengelolaan Pendidikan tahun 2026.'
WHERE NOT EXISTS (
    SELECT 1 FROM anggaran_pagu
    WHERE pemda_id = @pemda_id
      AND unit_id = @unit_disdikbud_id
      AND node_id = @node_program_id
      AND tahun = @tahun
      AND jenis_pagu = 'DPA'
);

SET @pagu_program_id := (
    SELECT id FROM anggaran_pagu
    WHERE pemda_id = @pemda_id
      AND unit_id = @unit_disdikbud_id
      AND node_id = @node_program_id
      AND tahun = @tahun
      AND jenis_pagu = 'DPA'
    LIMIT 1
);

INSERT INTO anggaran_realisasi (
    pagu_id, tahun, periode, realisasi_keuangan, realisasi_fisik, catatan
)
VALUES
(@pagu_program_id, @tahun, 'TRIWULAN_1', 4800000000.00, 22.50, 'Realisasi triwulan I.'),
(@pagu_program_id, @tahun, 'TRIWULAN_2', 10800000000.00, 48.00, 'Realisasi sampai triwulan II.'),
(@pagu_program_id, @tahun, 'TRIWULAN_3', 17700000000.00, 74.50, 'Realisasi sampai triwulan III.'),
(@pagu_program_id, @tahun, 'TRIWULAN_4', 23275000000.00, 96.20, 'Realisasi akhir tahun.')
ON DUPLICATE KEY UPDATE
    realisasi_keuangan = VALUES(realisasi_keuangan),
    realisasi_fisik = VALUES(realisasi_fisik),
    catatan = VALUES(catatan);

-- =========================================================
-- 8. PERJANJIAN KINERJA
-- =========================================================

INSERT INTO dokumen (
    pemda_id, unit_id, jenis_dokumen_id, tahun, periode_awal, periode_akhir,
    nomor_dokumen, judul, ringkasan, status, tanggal_dokumen, tanggal_penetapan, created_by
)
SELECT
@pemda_id, @unit_disdikbud_id, @jenis_pk_id, @tahun, @tahun, @tahun,
 'PK-DISDIKBUD-SIM-2026', 'Perjanjian Kinerja Dinas Pendidikan dan Kebudayaan Tahun 2026',
 'PK simulasi Kepala Dinas Pendidikan dan Kebudayaan tahun 2026.', 'DITETAPKAN',
 '2026-01-10', '2026-01-15', @user_kadis_id
WHERE NOT EXISTS (SELECT 1 FROM dokumen WHERE nomor_dokumen = 'PK-DISDIKBUD-SIM-2026');

SET @dok_pk_id := (SELECT id FROM dokumen WHERE nomor_dokumen = 'PK-DISDIKBUD-SIM-2026' LIMIT 1);

INSERT INTO pk_dokumen (
    pemda_id, unit_id, dokumen_id, tahun, nomor_pk, tanggal_pk, status
)
SELECT
    @pemda_id,
    @unit_disdikbud_id,
    @dok_pk_id,
    @tahun,
    'PK/Disdikbud/2026/001',
    '2026-01-15',
    'DITANDATANGANI'
WHERE NOT EXISTS (SELECT 1 FROM pk_dokumen WHERE nomor_pk = 'PK/Disdikbud/2026/001');

SET @pk_id := (SELECT id FROM pk_dokumen WHERE nomor_pk = 'PK/Disdikbud/2026/001' LIMIT 1);

INSERT INTO pk_pihak (
    pk_id, pihak, pegawai_id, nama, nip, jabatan, unit
)
VALUES
(@pk_id, 'PIHAK_PERTAMA', @pegawai_kadis_id, 'Drs. Ahmad Simulasi, M.Pd', '197001011990011001', 'Kepala Dinas Pendidikan dan Kebudayaan', 'Dinas Pendidikan dan Kebudayaan'),
(@pk_id, 'PIHAK_KEDUA', NULL, 'Bupati Simulasi', NULL, 'Bupati Hulu Sungai Selatan', 'Pemerintah Kabupaten Hulu Sungai Selatan')
ON DUPLICATE KEY UPDATE
    pegawai_id = VALUES(pegawai_id),
    nama = VALUES(nama),
    nip = VALUES(nip),
    jabatan = VALUES(jabatan),
    unit = VALUES(unit);

INSERT INTO pk_detail (
    pk_id, node_id, indikator_id, target_id, urutan, keterangan
)
VALUES
(@pk_id, @node_sasaran_opd_id, @indikator_opd_id, @target_opd_id, 1, 'IKU utama Kepala Dinas Pendidikan dan Kebudayaan.'),
(@pk_id, @node_sub_sd_id, @indikator_sd_id, @target_sd_id, 2, 'Output layanan pendidikan SD.'),
(@pk_id, @node_sub_smp_id, @indikator_smp_id, @target_smp_id, 3, 'Output layanan pendidikan SMP.')
ON DUPLICATE KEY UPDATE
    node_id = VALUES(node_id),
    urutan = VALUES(urutan),
    keterangan = VALUES(keterangan);

-- =========================================================
-- 9. RENCANA AKSI
-- =========================================================

INSERT INTO rencana_aksi (
    pemda_id, unit_id, node_id, indikator_id, tahun, nama_aksi, uraian,
    output_aksi, penanggung_jawab_pegawai_id, status
)
SELECT
@pemda_id, @unit_disdikbud_id, @node_sasaran_opd_id, @indikator_opd_id, @tahun,
 'Pendampingan sekolah berbasis rapor pendidikan',
 'Melakukan pemetaan, pendampingan, monitoring, dan evaluasi sekolah prioritas berbasis data.',
 'Sekolah prioritas mendapat pendampingan mutu pembelajaran dan tata kelola.',
 @pegawai_kadis_id, 'AKTIF'
WHERE NOT EXISTS (
    SELECT 1 FROM rencana_aksi
    WHERE pemda_id = @pemda_id
      AND unit_id = @unit_disdikbud_id
      AND tahun = @tahun
      AND nama_aksi = 'Pendampingan sekolah berbasis rapor pendidikan'
);

SET @renaksi_id := (
    SELECT id FROM rencana_aksi
    WHERE pemda_id = @pemda_id
      AND unit_id = @unit_disdikbud_id
      AND tahun = @tahun
      AND nama_aksi = 'Pendampingan sekolah berbasis rapor pendidikan'
    LIMIT 1
);

INSERT INTO rencana_aksi_detail (
    rencana_aksi_id, periode, target_output, realisasi_output,
    target_fisik, realisasi_fisik, target_keuangan, realisasi_keuangan,
    kendala, tindak_lanjut, status
)
VALUES
(@renaksi_id, 'TRIWULAN_1', 'Pemetaan 100 persen sekolah prioritas', 'Pemetaan selesai untuk SD dan SMP prioritas',
 25.00, 24.00, 5000000000.00, 4800000000.00, 'Beberapa data sekolah perlu validasi ulang.', 'Validasi bersama operator sekolah.', 'SELESAI'),
(@renaksi_id, 'TRIWULAN_2', 'Pendampingan tahap I pada 50 persen sekolah prioritas', 'Pendampingan tahap I terlaksana',
 50.00, 48.00, 11000000000.00, 10800000000.00, 'Sebagian sekolah membutuhkan jadwal ulang.', 'Pendampingan daring tambahan.', 'SELESAI'),
(@renaksi_id, 'TRIWULAN_3', 'Pendampingan tahap II dan monitoring', 'Pendampingan tahap II terlaksana',
 75.00, 74.50, 18000000000.00, 17700000000.00, 'Kelengkapan dokumen mutu belum seragam.', 'Klinik dokumen mutu sekolah.', 'SELESAI'),
(@renaksi_id, 'TRIWULAN_4', 'Evaluasi akhir dan laporan capaian', 'Evaluasi akhir terlaksana',
 100.00, 96.20, 24500000000.00, 23275000000.00, 'Sebagian capaian belum memenuhi target.', 'Rencana tindak lanjut tahun berikutnya.', 'SELESAI')
ON DUPLICATE KEY UPDATE
    target_output = VALUES(target_output),
    realisasi_output = VALUES(realisasi_output),
    target_fisik = VALUES(target_fisik),
    realisasi_fisik = VALUES(realisasi_fisik),
    target_keuangan = VALUES(target_keuangan),
    realisasi_keuangan = VALUES(realisasi_keuangan),
    kendala = VALUES(kendala),
    tindak_lanjut = VALUES(tindak_lanjut),
    status = VALUES(status);

-- =========================================================
-- 10. DOKUMEN BUKTI
-- =========================================================

INSERT INTO dokumen_bukti (
    dokumen_id, pemda_id, unit_id, tahun, judul, uraian,
    nama_file, file_path, mime_type, ukuran_byte, sha256, uploaded_by
)
SELECT
@dok_renja_id, @pemda_id, @unit_disdikbud_id, @tahun,
 'Bukti Renja Disdikbud Tahun 2026',
 'File simulasi bukti dokumen Renja.',
 'renja_disdikbud_2026.pdf',
 '/storage/sakip/2026/disdikbud/renja_disdikbud_2026.pdf',
 'application/pdf',
 1024000,
 NULL,
 @user_kadis_id
WHERE NOT EXISTS (
    SELECT 1 FROM dokumen_bukti
    WHERE pemda_id = @pemda_id
      AND unit_id = @unit_disdikbud_id
      AND tahun = @tahun
      AND nama_file = 'renja_disdikbud_2026.pdf'
)
UNION ALL
SELECT
@dok_pk_id, @pemda_id, @unit_disdikbud_id, @tahun,
 'Bukti PK Disdikbud Tahun 2026',
 'File simulasi bukti PK.',
 'pk_disdikbud_2026.pdf',
 '/storage/sakip/2026/disdikbud/pk_disdikbud_2026.pdf',
 'application/pdf',
 512000,
 NULL,
 @user_kadis_id
WHERE NOT EXISTS (
    SELECT 1 FROM dokumen_bukti
    WHERE pemda_id = @pemda_id
      AND unit_id = @unit_disdikbud_id
      AND tahun = @tahun
      AND nama_file = 'pk_disdikbud_2026.pdf'
);

SET @bukti_renja_id := (
    SELECT id FROM dokumen_bukti
    WHERE pemda_id = @pemda_id
      AND unit_id = @unit_disdikbud_id
      AND tahun = @tahun
      AND nama_file = 'renja_disdikbud_2026.pdf'
    ORDER BY id DESC
    LIMIT 1
);

-- =========================================================
-- 11. LKJIP OPD DAN LKJIP PEMDA
-- =========================================================

INSERT INTO dokumen (
    pemda_id, unit_id, jenis_dokumen_id, tahun, periode_awal, periode_akhir,
    nomor_dokumen, judul, ringkasan, status, tanggal_dokumen, tanggal_penetapan, created_by
)
SELECT
@pemda_id, @unit_disdikbud_id, @jenis_lkjip_opd_id, @tahun, @tahun, @tahun,
 'LKJIP-DISDIKBUD-SIM-2026', 'LKJIP Dinas Pendidikan dan Kebudayaan Tahun 2026',
 'LKJIP simulasi Disdikbud tahun 2026.', 'DIAJUKAN',
 '2027-01-20', NULL, @user_kadis_id
WHERE NOT EXISTS (SELECT 1 FROM dokumen WHERE nomor_dokumen = 'LKJIP-DISDIKBUD-SIM-2026');

SET @dok_lkjip_opd_id := (SELECT id FROM dokumen WHERE nomor_dokumen = 'LKJIP-DISDIKBUD-SIM-2026' LIMIT 1);

INSERT INTO lkjip_dokumen (
    pemda_id, unit_id, dokumen_id, tahun, level_laporan, status, tanggal_laporan
)
SELECT
@pemda_id, @unit_disdikbud_id, @dok_lkjip_opd_id, @tahun, 'OPD', 'DIREVIU', '2027-01-20'
WHERE NOT EXISTS (SELECT 1 FROM lkjip_dokumen WHERE dokumen_id = @dok_lkjip_opd_id);

SET @lkjip_opd_id := (SELECT id FROM lkjip_dokumen WHERE dokumen_id = @dok_lkjip_opd_id LIMIT 1);

INSERT INTO lkjip_bab (
    lkjip_id, kode_bab, judul, isi, urutan
)
VALUES
(@lkjip_opd_id, 'BAB-I', 'Pendahuluan', 'Bab pendahuluan LKJIP OPD simulasi.', 1),
(@lkjip_opd_id, 'BAB-II', 'Perencanaan Kinerja', 'Bab perencanaan kinerja memuat tujuan, sasaran, indikator, target, dan PK.', 2),
(@lkjip_opd_id, 'BAB-III', 'Akuntabilitas Kinerja', 'Bab akuntabilitas kinerja memuat capaian, analisis, efisiensi, dan perbaikan.', 3),
(@lkjip_opd_id, 'BAB-IV', 'Penutup', 'Bab penutup LKJIP OPD simulasi.', 4)
ON DUPLICATE KEY UPDATE
    judul = VALUES(judul),
    isi = VALUES(isi),
    urutan = VALUES(urutan);

INSERT INTO lkjip_capaian (
    lkjip_id, node_id, indikator_id, target_id, realisasi_id, capaian_id,
    narasi_analisis, narasi_efisiensi, rekomendasi
)
SELECT
    @lkjip_opd_id,
    c_node.id,
    i.id,
    t.id,
    r.id,
    c.id,
    c.analisis_capaian,
    c.analisis_efisiensi,
    c.rekomendasi_perbaikan
FROM sakip_capaian c
JOIN sakip_indikator i ON i.id = c.indikator_id
JOIN sakip_kinerja_node c_node ON c_node.id = i.node_id
JOIN sakip_target t ON t.id = c.target_id
JOIN sakip_realisasi r ON r.id = c.realisasi_id
WHERE i.id IN (@indikator_opd_id, @indikator_sd_id, @indikator_smp_id)
ON DUPLICATE KEY UPDATE
    node_id = VALUES(node_id),
    target_id = VALUES(target_id),
    realisasi_id = VALUES(realisasi_id),
    capaian_id = VALUES(capaian_id),
    narasi_analisis = VALUES(narasi_analisis),
    narasi_efisiensi = VALUES(narasi_efisiensi),
    rekomendasi = VALUES(rekomendasi);

INSERT INTO lkjip_reviu (
    lkjip_id, reviewer_user_id, tanggal_reviu, hasil_reviu, catatan_umum, catatan_perbaikan
)
SELECT
@lkjip_opd_id, @user_bagorg_id, '2027-01-25', 'LAYAK_DENGAN_CATATAN',
 'LKJIP telah memuat target, realisasi, capaian, dan analisis awal.',
 'Perkuat narasi efisiensi dan keterkaitan rekomendasi dengan rencana aksi tahun berikutnya.'
WHERE NOT EXISTS (
    SELECT 1 FROM lkjip_reviu
    WHERE lkjip_id = @lkjip_opd_id
      AND reviewer_user_id = @user_bagorg_id
      AND tanggal_reviu = '2027-01-25'
);

INSERT INTO dokumen (
    pemda_id, unit_id, jenis_dokumen_id, tahun, periode_awal, periode_akhir,
    nomor_dokumen, judul, ringkasan, status, tanggal_dokumen, tanggal_penetapan, created_by
)
SELECT
@pemda_id, @unit_pemda_id, @jenis_lkjip_pemda_id, @tahun, @tahun, @tahun,
 'LKJIP-PEMDA-SIM-2026', 'LKJIP Pemerintah Kabupaten Hulu Sungai Selatan Tahun 2026',
 'LKJIP simulasi pemerintah kabupaten tahun 2026.', 'DIAJUKAN',
 '2027-02-15', NULL, @user_bagorg_id
WHERE NOT EXISTS (SELECT 1 FROM dokumen WHERE nomor_dokumen = 'LKJIP-PEMDA-SIM-2026');

SET @dok_lkjip_pemda_id := (SELECT id FROM dokumen WHERE nomor_dokumen = 'LKJIP-PEMDA-SIM-2026' LIMIT 1);

INSERT INTO lkjip_dokumen (
    pemda_id, unit_id, dokumen_id, tahun, level_laporan, status, tanggal_laporan
)
SELECT
@pemda_id, @unit_pemda_id, @dok_lkjip_pemda_id, @tahun, 'PEMDA', 'DRAFT', '2027-02-15'
WHERE NOT EXISTS (SELECT 1 FROM lkjip_dokumen WHERE dokumen_id = @dok_lkjip_pemda_id);

SET @lkjip_pemda_id := (SELECT id FROM lkjip_dokumen WHERE dokumen_id = @dok_lkjip_pemda_id LIMIT 1);

INSERT INTO lkjip_capaian (
    lkjip_id, node_id, indikator_id, target_id, realisasi_id, capaian_id,
    narasi_analisis, narasi_efisiensi, rekomendasi
)
SELECT
    @lkjip_pemda_id,
    c_node.id,
    i.id,
    t.id,
    r.id,
    c.id,
    c.analisis_capaian,
    c.analisis_efisiensi,
    c.rekomendasi_perbaikan
FROM sakip_capaian c
JOIN sakip_indikator i ON i.id = c.indikator_id
JOIN sakip_kinerja_node c_node ON c_node.id = i.node_id
JOIN sakip_target t ON t.id = c.target_id
JOIN sakip_realisasi r ON r.id = c.realisasi_id
WHERE i.id = @indikator_daerah_id
ON DUPLICATE KEY UPDATE
    node_id = VALUES(node_id),
    target_id = VALUES(target_id),
    realisasi_id = VALUES(realisasi_id),
    capaian_id = VALUES(capaian_id),
    narasi_analisis = VALUES(narasi_analisis),
    narasi_efisiensi = VALUES(narasi_efisiensi),
    rekomendasi = VALUES(rekomendasi);

-- =========================================================
-- 12. TEMPLATE LKE DAN EVALUASI AKIP
-- =========================================================

INSERT INTO lke_template (kode, nama, tahun_berlaku, regulasi_id, total_bobot, is_aktif)
SELECT
    'LKE_AKIP_88_2021',
    'LKE AKIP berdasarkan PermenPANRB 88 Tahun 2021',
    2021,
    (SELECT id FROM ref_regulasi WHERE kode = 'PERMENPANRB_88_2021' LIMIT 1),
    100.00,
    1
WHERE NOT EXISTS (
    SELECT 1 FROM lke_template WHERE kode = 'LKE_AKIP_88_2021'
);

SET @template_lke_id := (SELECT id FROM lke_template WHERE kode = 'LKE_AKIP_88_2021' LIMIT 1);

INSERT INTO lke_komponen (template_id, kode, nama, bobot, urutan)
SELECT @template_lke_id, 'PERENCANAAN', 'Perencanaan Kinerja', 30.00, 1
WHERE NOT EXISTS (SELECT 1 FROM lke_komponen WHERE template_id = @template_lke_id AND kode = 'PERENCANAAN');

INSERT INTO lke_komponen (template_id, kode, nama, bobot, urutan)
SELECT @template_lke_id, 'PENGUKURAN', 'Pengukuran Kinerja', 30.00, 2
WHERE NOT EXISTS (SELECT 1 FROM lke_komponen WHERE template_id = @template_lke_id AND kode = 'PENGUKURAN');

INSERT INTO lke_komponen (template_id, kode, nama, bobot, urutan)
SELECT @template_lke_id, 'PELAPORAN', 'Pelaporan Kinerja', 15.00, 3
WHERE NOT EXISTS (SELECT 1 FROM lke_komponen WHERE template_id = @template_lke_id AND kode = 'PELAPORAN');

INSERT INTO lke_komponen (template_id, kode, nama, bobot, urutan)
SELECT @template_lke_id, 'EVALUASI_INTERNAL', 'Evaluasi Akuntabilitas Kinerja Internal', 25.00, 4
WHERE NOT EXISTS (SELECT 1 FROM lke_komponen WHERE template_id = @template_lke_id AND kode = 'EVALUASI_INTERNAL');

SET @komp_perencanaan_id := (SELECT id FROM lke_komponen WHERE template_id = @template_lke_id AND kode = 'PERENCANAAN' LIMIT 1);
SET @komp_pengukuran_id := (SELECT id FROM lke_komponen WHERE template_id = @template_lke_id AND kode = 'PENGUKURAN' LIMIT 1);
SET @komp_pelaporan_id := (SELECT id FROM lke_komponen WHERE template_id = @template_lke_id AND kode = 'PELAPORAN' LIMIT 1);
SET @komp_evaluasi_id := (SELECT id FROM lke_komponen WHERE template_id = @template_lke_id AND kode = 'EVALUASI_INTERNAL' LIMIT 1);

INSERT INTO lke_subkomponen (komponen_id, kode, nama, bobot, urutan)
SELECT @komp_perencanaan_id, 'KUALITAS_RENSTRA', 'Kualitas Renstra dan cascading kinerja', 15.00, 1
WHERE NOT EXISTS (SELECT 1 FROM lke_subkomponen WHERE komponen_id = @komp_perencanaan_id AND kode = 'KUALITAS_RENSTRA');

INSERT INTO lke_subkomponen (komponen_id, kode, nama, bobot, urutan)
SELECT @komp_pengukuran_id, 'KUALITAS_INDIKATOR', 'Kualitas indikator dan pengukuran kinerja', 15.00, 1
WHERE NOT EXISTS (SELECT 1 FROM lke_subkomponen WHERE komponen_id = @komp_pengukuran_id AND kode = 'KUALITAS_INDIKATOR');

INSERT INTO lke_subkomponen (komponen_id, kode, nama, bobot, urutan)
SELECT @komp_pelaporan_id, 'KUALITAS_LKJIP', 'Kualitas laporan kinerja', 10.00, 1
WHERE NOT EXISTS (SELECT 1 FROM lke_subkomponen WHERE komponen_id = @komp_pelaporan_id AND kode = 'KUALITAS_LKJIP');

INSERT INTO lke_subkomponen (komponen_id, kode, nama, bobot, urutan)
SELECT @komp_evaluasi_id, 'TINDAK_LANJUT', 'Pemanfaatan evaluasi dan tindak lanjut', 15.00, 1
WHERE NOT EXISTS (SELECT 1 FROM lke_subkomponen WHERE komponen_id = @komp_evaluasi_id AND kode = 'TINDAK_LANJUT');

SET @sub_lke_renstra_id := (SELECT id FROM lke_subkomponen WHERE komponen_id = @komp_perencanaan_id AND kode = 'KUALITAS_RENSTRA' LIMIT 1);
SET @sub_lke_indikator_id := (SELECT id FROM lke_subkomponen WHERE komponen_id = @komp_pengukuran_id AND kode = 'KUALITAS_INDIKATOR' LIMIT 1);
SET @sub_lke_lkjip_id := (SELECT id FROM lke_subkomponen WHERE komponen_id = @komp_pelaporan_id AND kode = 'KUALITAS_LKJIP' LIMIT 1);
SET @sub_lke_tl_id := (SELECT id FROM lke_subkomponen WHERE komponen_id = @komp_evaluasi_id AND kode = 'TINDAK_LANJUT' LIMIT 1);

INSERT INTO lke_kriteria (
    subkomponen_id, kode, pertanyaan, bobot, tipe_jawaban, membutuhkan_bukti, urutan
)
SELECT @sub_lke_renstra_id, 'P1', 'Renstra telah memuat tujuan, sasaran, indikator, target, dan cascading yang selaras dengan RPJMD.', 15.00, 'NILAI', 1, 1
WHERE NOT EXISTS (SELECT 1 FROM lke_kriteria WHERE subkomponen_id = @sub_lke_renstra_id AND kode = 'P1');

INSERT INTO lke_kriteria (
    subkomponen_id, kode, pertanyaan, bobot, tipe_jawaban, membutuhkan_bukti, urutan
)
SELECT @sub_lke_indikator_id, 'U1', 'Indikator kinerja telah memenuhi definisi operasional, formula, sumber data, target, dan penanggung jawab.', 15.00, 'NILAI', 1, 1
WHERE NOT EXISTS (SELECT 1 FROM lke_kriteria WHERE subkomponen_id = @sub_lke_indikator_id AND kode = 'U1');

INSERT INTO lke_kriteria (
    subkomponen_id, kode, pertanyaan, bobot, tipe_jawaban, membutuhkan_bukti, urutan
)
SELECT @sub_lke_lkjip_id, 'L1', 'LKJIP telah menyajikan capaian kinerja, analisis, efisiensi, kendala, dan rekomendasi perbaikan.', 10.00, 'NILAI', 1, 1
WHERE NOT EXISTS (SELECT 1 FROM lke_kriteria WHERE subkomponen_id = @sub_lke_lkjip_id AND kode = 'L1');

INSERT INTO lke_kriteria (
    subkomponen_id, kode, pertanyaan, bobot, tipe_jawaban, membutuhkan_bukti, urutan
)
SELECT @sub_lke_tl_id, 'E1', 'Rekomendasi hasil evaluasi telah ditindaklanjuti dan dimanfaatkan untuk perbaikan kinerja.', 15.00, 'NILAI', 1, 1
WHERE NOT EXISTS (SELECT 1 FROM lke_kriteria WHERE subkomponen_id = @sub_lke_tl_id AND kode = 'E1');

SET @krit_renstra_id := (SELECT id FROM lke_kriteria WHERE subkomponen_id = @sub_lke_renstra_id AND kode = 'P1' LIMIT 1);
SET @krit_indikator_id := (SELECT id FROM lke_kriteria WHERE subkomponen_id = @sub_lke_indikator_id AND kode = 'U1' LIMIT 1);
SET @krit_lkjip_id := (SELECT id FROM lke_kriteria WHERE subkomponen_id = @sub_lke_lkjip_id AND kode = 'L1' LIMIT 1);
SET @krit_tl_id := (SELECT id FROM lke_kriteria WHERE subkomponen_id = @sub_lke_tl_id AND kode = 'E1' LIMIT 1);

INSERT INTO evaluasi_akip (
    pemda_id, tahun, template_id, level_evaluasi, jenis_evaluasi,
    tanggal_mulai, tanggal_selesai, status, ketua_tim_user_id, catatan_umum
)
SELECT
@pemda_id, @tahun, @template_lke_id, 'OPD', 'INTERNAL_INSPEKTORAT',
 '2027-02-01', '2027-02-20', 'SELESAI', @user_irban_id,
 'Evaluasi internal AKIP simulasi untuk Disdikbud tahun 2026.'
WHERE NOT EXISTS (
    SELECT 1 FROM evaluasi_akip
    WHERE pemda_id = @pemda_id
      AND tahun = @tahun
      AND template_id = @template_lke_id
      AND level_evaluasi = 'OPD'
      AND jenis_evaluasi = 'INTERNAL_INSPEKTORAT'
);

SET @evaluasi_id := (
    SELECT id FROM evaluasi_akip
    WHERE pemda_id = @pemda_id
      AND tahun = @tahun
      AND template_id = @template_lke_id
      AND level_evaluasi = 'OPD'
      AND jenis_evaluasi = 'INTERNAL_INSPEKTORAT'
    LIMIT 1
);

SET @predikat_bb_id := (SELECT id FROM ref_predikat_sakip WHERE kode = 'BB' LIMIT 1);

INSERT INTO evaluasi_unit (
    evaluasi_id, unit_id, nilai_total, predikat_id, ringkasan_hasil, status
)
SELECT
@evaluasi_id, @unit_disdikbud_id, 74.25, @predikat_bb_id,
 'Akuntabilitas kinerja Disdikbud berada pada kategori sangat baik, namun pengukuran triwulanan dan tindak lanjut perlu diperkuat.',
 'SELESAI'
WHERE NOT EXISTS (SELECT 1 FROM evaluasi_unit WHERE evaluasi_id = @evaluasi_id AND unit_id = @unit_disdikbud_id);

SET @evaluasi_unit_id := (
    SELECT id FROM evaluasi_unit
    WHERE evaluasi_id = @evaluasi_id
      AND unit_id = @unit_disdikbud_id
    LIMIT 1
);

INSERT INTO evaluasi_lke_jawaban (
    evaluasi_unit_id, kriteria_id, nilai, jawaban_teks, catatan, dokumen_bukti_id,
    penilai_user_id, dinilai_at
)
VALUES
(@evaluasi_unit_id, @krit_renstra_id, 12.00, 'Memadai',
 'Renstra dan cascading tersedia, namun logika kontribusi antar level perlu dipertajam.', @bukti_renja_id,
 @user_irban_id, '2027-02-10 09:00:00'),
(@evaluasi_unit_id, @krit_indikator_id, 11.25, 'Cukup memadai',
 'Sebagian indikator sudah memiliki definisi dan formula, tetapi kualitas sumber data perlu diperkuat.', @bukti_renja_id,
 @user_irban_id, '2027-02-10 09:15:00'),
(@evaluasi_unit_id, @krit_lkjip_id, 8.00, 'Memadai',
 'LKJIP menyajikan capaian dan analisis, namun analisis efisiensi belum dalam.', @bukti_renja_id,
 @user_irban_id, '2027-02-10 09:30:00'),
(@evaluasi_unit_id, @krit_tl_id, 10.50, 'Cukup memadai',
 'Tindak lanjut tersedia, namun pemantauan progres perlu dibuat lebih periodik.', @bukti_renja_id,
 @user_irban_id, '2027-02-10 09:45:00')
ON DUPLICATE KEY UPDATE
    nilai = VALUES(nilai),
    jawaban_teks = VALUES(jawaban_teks),
    catatan = VALUES(catatan),
    dokumen_bukti_id = VALUES(dokumen_bukti_id),
    penilai_user_id = VALUES(penilai_user_id),
    dinilai_at = VALUES(dinilai_at);

-- =========================================================
-- 13. TEMUAN, REKOMENDASI, TINDAK LANJUT
-- =========================================================

INSERT INTO evaluasi_temuan (
    evaluasi_unit_id, komponen_id, kriteria_id, jenis_temuan, uraian, sebab, akibat, tingkat_risiko
)
SELECT
@evaluasi_unit_id, @komp_pengukuran_id, @krit_indikator_id, 'PELUANG_PERBAIKAN',
 'Pengukuran kinerja triwulanan belum sepenuhnya digunakan sebagai dasar pengambilan keputusan pimpinan.',
 'Dashboard monitoring belum terintegrasi dengan data realisasi seluruh bidang.',
 'Respons perbaikan berpotensi terlambat karena data kinerja belum tersedia real time.',
 'SEDANG'
WHERE NOT EXISTS (
    SELECT 1 FROM evaluasi_temuan
    WHERE evaluasi_unit_id = @evaluasi_unit_id
      AND kriteria_id = @krit_indikator_id
      AND jenis_temuan = 'PELUANG_PERBAIKAN'
);

SET @temuan_id := (
    SELECT id FROM evaluasi_temuan
    WHERE evaluasi_unit_id = @evaluasi_unit_id
      AND kriteria_id = @krit_indikator_id
      AND jenis_temuan = 'PELUANG_PERBAIKAN'
    LIMIT 1
);

INSERT INTO evaluasi_rekomendasi (
    temuan_id, rekomendasi, prioritas, batas_waktu, unit_penanggung_jawab_id, status
)
SELECT
@temuan_id,
 'Membangun dashboard monitoring triwulanan dan menetapkan jadwal rapat evaluasi kinerja setiap triwulan.',
 'TINGGI',
 '2027-06-30',
 @unit_disdikbud_id,
 'DITINDAKLANJUTI'
WHERE NOT EXISTS (
    SELECT 1 FROM evaluasi_rekomendasi
    WHERE temuan_id = @temuan_id
      AND rekomendasi = 'Membangun dashboard monitoring triwulanan dan menetapkan jadwal rapat evaluasi kinerja setiap triwulan.'
);

SET @rekomendasi_id := (
    SELECT id FROM evaluasi_rekomendasi
    WHERE temuan_id = @temuan_id
      AND rekomendasi = 'Membangun dashboard monitoring triwulanan dan menetapkan jadwal rapat evaluasi kinerja setiap triwulan.'
    LIMIT 1
);

INSERT INTO evaluasi_tindak_lanjut (
    rekomendasi_id, uraian_tindak_lanjut, tanggal_tindak_lanjut, progres_persen,
    status, verifikator_user_id, catatan_verifikasi, verified_at
)
SELECT
@rekomendasi_id,
 'Disdikbud menyusun rencana pembangunan dashboard monitoring triwulanan dan menetapkan format rapat evaluasi kinerja.',
 '2027-03-15',
 40.00,
 'VALID',
 @user_irban_id,
 'Tindak lanjut awal valid, perlu pemantauan lanjutan sampai dashboard aktif.',
 '2027-03-20 10:00:00'
WHERE NOT EXISTS (
    SELECT 1 FROM evaluasi_tindak_lanjut
    WHERE rekomendasi_id = @rekomendasi_id
      AND tanggal_tindak_lanjut = '2027-03-15'
);

SET @tindak_lanjut_id := (
    SELECT id FROM evaluasi_tindak_lanjut
    WHERE rekomendasi_id = @rekomendasi_id
      AND tanggal_tindak_lanjut = '2027-03-15'
    LIMIT 1
);

INSERT INTO evaluasi_tindak_lanjut_bukti (
    tindak_lanjut_id, dokumen_bukti_id
)
VALUES
(@tindak_lanjut_id, @bukti_renja_id)
ON DUPLICATE KEY UPDATE
    dokumen_bukti_id = VALUES(dokumen_bukti_id);

-- =========================================================
-- 14. WORKFLOW DAN AI REVIEW
-- =========================================================

INSERT INTO workflow_instance (
    pemda_id, unit_id, objek_tipe, objek_id, nama_workflow, status, created_by
)
SELECT
@pemda_id, @unit_disdikbud_id, 'LKJIP_OPD', @lkjip_opd_id, 'Review LKJIP OPD Tahun 2026', 'SELESAI', @user_kadis_id
WHERE NOT EXISTS (
    SELECT 1 FROM workflow_instance
    WHERE objek_tipe = 'LKJIP_OPD'
      AND objek_id = @lkjip_opd_id
      AND nama_workflow = 'Review LKJIP OPD Tahun 2026'
);

SET @workflow_id := (
    SELECT id FROM workflow_instance
    WHERE objek_tipe = 'LKJIP_OPD'
      AND objek_id = @lkjip_opd_id
      AND nama_workflow = 'Review LKJIP OPD Tahun 2026'
    LIMIT 1
);

INSERT INTO workflow_step (
    workflow_id, urutan, nama_step, role_id, user_id, status, acted_at, catatan
)
VALUES
(@workflow_id, 1, 'Input LKJIP oleh OPD', @role_kepala_opd_id, @user_kadis_id, 'DISETUJUI', '2027-01-20 14:00:00', 'LKJIP disampaikan oleh OPD.'),
(@workflow_id, 2, 'Reviu Bagian Organisasi', @role_bagorg_id, @user_bagorg_id, 'DISETUJUI', '2027-01-25 09:00:00', 'LKJIP layak dengan catatan.'),
(@workflow_id, 3, 'Evaluasi Inspektorat', @role_inspektorat_id, @user_irban_id, 'DISETUJUI', '2027-02-20 15:00:00', 'Evaluasi internal selesai.')
ON DUPLICATE KEY UPDATE
    nama_step = VALUES(nama_step),
    role_id = VALUES(role_id),
    user_id = VALUES(user_id),
    status = VALUES(status),
    acted_at = VALUES(acted_at),
    catatan = VALUES(catatan);

INSERT INTO workflow_log (
    workflow_id, step_id, user_id, aksi, catatan
)
SELECT @workflow_id, id, user_id, status, catatan
FROM workflow_step
WHERE workflow_id = @workflow_id
  AND NOT EXISTS (
      SELECT 1 FROM workflow_log
      WHERE workflow_log.workflow_id = @workflow_id
        AND workflow_log.step_id = workflow_step.id
        AND workflow_log.aksi = workflow_step.status
  );

INSERT INTO ai_review_job (
    pemda_id, unit_id, objek_tipe, objek_id, jenis_review,
    prompt_ringkas, status, requested_by, requested_at, finished_at
)
SELECT
@pemda_id, @unit_disdikbud_id, 'LKJIP_OPD', @lkjip_opd_id, 'LKJIP',
 'Review kualitas LKJIP Disdikbud tahun 2026 berdasarkan keterkaitan target, realisasi, analisis, efisiensi, dan rekomendasi.',
 'SELESAI',
 @user_bagorg_id,
 '2027-01-24 09:00:00',
 '2027-01-24 09:05:00'
WHERE NOT EXISTS (
    SELECT 1 FROM ai_review_job
    WHERE objek_tipe = 'LKJIP_OPD'
      AND objek_id = @lkjip_opd_id
      AND jenis_review = 'LKJIP'
);

SET @ai_job_id := (
    SELECT id FROM ai_review_job
    WHERE objek_tipe = 'LKJIP_OPD'
      AND objek_id = @lkjip_opd_id
      AND jenis_review = 'LKJIP'
    LIMIT 1
);

INSERT INTO ai_review_result (
    job_id, skor, ringkasan, masalah, rekomendasi, json_result
)
VALUES
(@ai_job_id,
 78.50,
 'LKJIP cukup baik dan telah memuat capaian utama, namun analisis efisiensi dan tindak lanjut perlu diperkuat.',
 'Analisis efisiensi belum mengaitkan capaian fisik, realisasi keuangan, dan outcome secara kuat.',
 'Tambahkan analisis sebab akibat, efisiensi anggaran, dan rencana perbaikan triwulanan.',
 JSON_OBJECT(
     'aspek', JSON_ARRAY('capaian', 'efisiensi', 'rekomendasi'),
     'skor_capaian', 82.00,
     'skor_efisiensi', 70.00,
     'skor_rekomendasi', 78.00
 ))
ON DUPLICATE KEY UPDATE
    skor = VALUES(skor),
    ringkasan = VALUES(ringkasan),
    masalah = VALUES(masalah),
    rekomendasi = VALUES(rekomendasi),
    json_result = VALUES(json_result);

-- =========================================================
-- 15. AUDIT AWAL
-- =========================================================

INSERT INTO audit_log (
    user_id, pemda_id, unit_id, aksi, tabel, record_id,
    before_json, after_json, ip_address, user_agent
)
SELECT
@user_bagorg_id, @pemda_id, @unit_bagorg_id, 'SEED_DATA_SIMULASI', 'sakip_pemda', @pemda_id,
 NULL,
 JSON_OBJECT(
     'tahun', @tahun,
     'scope', 'Simulasi SAKIP Kabupaten',
     'opd_sample', 'Dinas Pendidikan dan Kebudayaan',
     'status', 'completed'
 ),
 '127.0.0.1',
 'mysql-seed'
WHERE NOT EXISTS (
    SELECT 1 FROM audit_log
    WHERE aksi = 'SEED_DATA_SIMULASI'
      AND tabel = 'sakip_pemda'
      AND record_id = @pemda_id
);

COMMIT;

-- =========================================================
-- 16. CEK RINGKAS SETELAH SEED
-- =========================================================

SELECT 'pemda' AS objek, COUNT(*) AS jumlah FROM pemda
UNION ALL
SELECT 'unit_organisasi', COUNT(*) FROM unit_organisasi
UNION ALL
SELECT 'dokumen', COUNT(*) FROM dokumen
UNION ALL
SELECT 'sakip_kinerja_node', COUNT(*) FROM sakip_kinerja_node
UNION ALL
SELECT 'sakip_indikator', COUNT(*) FROM sakip_indikator
UNION ALL
SELECT 'sakip_target', COUNT(*) FROM sakip_target
UNION ALL
SELECT 'sakip_realisasi', COUNT(*) FROM sakip_realisasi
UNION ALL
SELECT 'sakip_capaian', COUNT(*) FROM sakip_capaian
UNION ALL
SELECT 'pk_dokumen', COUNT(*) FROM pk_dokumen
UNION ALL
SELECT 'lkjip_dokumen', COUNT(*) FROM lkjip_dokumen
UNION ALL
SELECT 'evaluasi_akip', COUNT(*) FROM evaluasi_akip
UNION ALL
SELECT 'evaluasi_rekomendasi', COUNT(*) FROM evaluasi_rekomendasi
UNION ALL
SELECT 'evaluasi_tindak_lanjut', COUNT(*) FROM evaluasi_tindak_lanjut;
