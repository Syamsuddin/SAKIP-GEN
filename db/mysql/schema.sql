CREATE DATABASE IF NOT EXISTS sakip_pemda
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE sakip_pemda;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS audit_log;
DROP TABLE IF EXISTS ai_review_result;
DROP TABLE IF EXISTS ai_review_job;
DROP TABLE IF EXISTS workflow_log;
DROP TABLE IF EXISTS workflow_step;
DROP TABLE IF EXISTS workflow_instance;
DROP TABLE IF EXISTS evaluasi_tindak_lanjut_bukti;
DROP TABLE IF EXISTS evaluasi_tindak_lanjut;
DROP TABLE IF EXISTS evaluasi_rekomendasi;
DROP TABLE IF EXISTS evaluasi_temuan;
DROP TABLE IF EXISTS evaluasi_lke_jawaban;
DROP TABLE IF EXISTS evaluasi_unit;
DROP TABLE IF EXISTS evaluasi_akip;
DROP TABLE IF EXISTS lke_kriteria;
DROP TABLE IF EXISTS lke_subkomponen;
DROP TABLE IF EXISTS lke_komponen;
DROP TABLE IF EXISTS lke_template;
DROP TABLE IF EXISTS lkjip_reviu;
DROP TABLE IF EXISTS lkjip_capaian;
DROP TABLE IF EXISTS lkjip_bab;
DROP TABLE IF EXISTS lkjip_dokumen;
DROP TABLE IF EXISTS pk_detail;
DROP TABLE IF EXISTS pk_pihak;
DROP TABLE IF EXISTS pk_dokumen;
DROP TABLE IF EXISTS rencana_aksi_detail;
DROP TABLE IF EXISTS rencana_aksi;
DROP TABLE IF EXISTS anggaran_realisasi;
DROP TABLE IF EXISTS anggaran_pagu;
DROP TABLE IF EXISTS sakip_capaian;
DROP TABLE IF EXISTS sakip_realisasi;
DROP TABLE IF EXISTS sakip_target;
DROP TABLE IF EXISTS sakip_indikator;
DROP TABLE IF EXISTS sakip_cascading_relasi;
DROP TABLE IF EXISTS sakip_crosscutting_relasi;
DROP TABLE IF EXISTS sakip_kinerja_node;
DROP TABLE IF EXISTS renja_dokumen;
DROP TABLE IF EXISTS rkpd_dokumen;
DROP TABLE IF EXISTS renstra_dokumen;
DROP TABLE IF EXISTS rpjmd_dokumen;
DROP TABLE IF EXISTS dokumen_relasi;
DROP TABLE IF EXISTS dokumen_bukti;
DROP TABLE IF EXISTS dokumen_versi;
DROP TABLE IF EXISTS dokumen;
DROP TABLE IF EXISTS app_role_permission;
DROP TABLE IF EXISTS app_user_role;
DROP TABLE IF EXISTS app_permission;
DROP TABLE IF EXISTS app_role;
DROP TABLE IF EXISTS app_user;
DROP TABLE IF EXISTS pegawai;
DROP TABLE IF EXISTS jabatan;
DROP TABLE IF EXISTS unit_organisasi;
DROP TABLE IF EXISTS pemda;
DROP TABLE IF EXISTS ref_sub_kegiatan;
DROP TABLE IF EXISTS ref_kegiatan;
DROP TABLE IF EXISTS ref_program;
DROP TABLE IF EXISTS ref_bidang_urusan;
DROP TABLE IF EXISTS ref_urusan;
DROP TABLE IF EXISTS ref_predikat_sakip;
DROP TABLE IF EXISTS ref_dokumen_jenis;
DROP TABLE IF EXISTS ref_satuan;
DROP TABLE IF EXISTS ref_tahun;
DROP TABLE IF EXISTS ref_regulasi;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE ref_tahun (
    tahun SMALLINT PRIMARY KEY,
    nama_tahun VARCHAR(20) NOT NULL,
    is_aktif TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_ref_tahun_tahun CHECK (tahun BETWEEN 1900 AND 2200),
    CONSTRAINT chk_ref_tahun_aktif CHECK (is_aktif IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ref_satuan (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    kode VARCHAR(30) NOT NULL UNIQUE,
    nama VARCHAR(100) NOT NULL,
    tipe ENUM('JUMLAH','PERSEN','RUPIAH','INDEKS','RASIO','HARI','BULAN','TAHUN','PREDIKAT','LAINNYA') NOT NULL DEFAULT 'LAINNYA',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ref_regulasi (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    kode VARCHAR(50) NOT NULL UNIQUE,
    nama VARCHAR(255) NOT NULL,
    nomor VARCHAR(100) NULL,
    tahun SMALLINT NULL,
    jenis ENUM('UU','PP','PERPRES','PERMEN','PERDA','PERKADA','SE','PEDOMAN','LAINNYA') NOT NULL,
    sumber_url TEXT NULL,
    ringkasan TEXT NULL,
    status_berlaku ENUM('BERLAKU','DICABUT','DIUBAH','ARSIP') NOT NULL DEFAULT 'BERLAKU',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_ref_regulasi_tahun CHECK (tahun IS NULL OR tahun BETWEEN 1900 AND 2200)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ref_dokumen_jenis (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    kode VARCHAR(50) NOT NULL UNIQUE,
    nama VARCHAR(150) NOT NULL,
    kelompok ENUM('PERENCANAAN','PENGUKURAN','PELAPORAN','EVALUASI','ANGGARAN','BUKTI','REGULASI','LAINNYA') NOT NULL,
    level_dokumen ENUM('PEMDA','OPD','UNIT','INDIVIDU','UMUM') NOT NULL DEFAULT 'UMUM',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ref_predikat_sakip (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    kode VARCHAR(10) NOT NULL UNIQUE,
    nama VARCHAR(100) NOT NULL,
    nilai_min DECIMAL(6,2) NOT NULL,
    nilai_max DECIMAL(6,2) NOT NULL,
    uraian TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_ref_predikat_nilai CHECK (nilai_min >= 0 AND nilai_max >= nilai_min)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ref_urusan (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    kode VARCHAR(20) NOT NULL UNIQUE,
    nama VARCHAR(255) NOT NULL,
    jenis ENUM('WAJIB_PELAYANAN_DASAR','WAJIB_NON_PELAYANAN_DASAR','PILIHAN','PENUNJANG','PENGAWASAN','KEWILAYAHAN','PEMERINTAHAN_UMUM') NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ref_bidang_urusan (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    urusan_id BIGINT UNSIGNED NOT NULL,
    kode VARCHAR(30) NOT NULL UNIQUE,
    nama VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (urusan_id) REFERENCES ref_urusan(id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ref_program (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    bidang_urusan_id BIGINT UNSIGNED NOT NULL,
    kode VARCHAR(50) NOT NULL UNIQUE,
    nama VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (bidang_urusan_id) REFERENCES ref_bidang_urusan(id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ref_kegiatan (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    program_id BIGINT UNSIGNED NOT NULL,
    kode VARCHAR(50) NOT NULL UNIQUE,
    nama VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (program_id) REFERENCES ref_program(id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ref_sub_kegiatan (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    kegiatan_id BIGINT UNSIGNED NOT NULL,
    kode VARCHAR(50) NOT NULL UNIQUE,
    nama VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (kegiatan_id) REFERENCES ref_kegiatan(id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE pemda (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    parent_id BIGINT UNSIGNED NULL,
    kode_wilayah VARCHAR(20) NOT NULL UNIQUE,
    nama VARCHAR(255) NOT NULL,
    level_pemda ENUM('PROVINSI','KABUPATEN','KOTA') NOT NULL,
    nama_kepala_daerah VARCHAR(150) NULL,
    jabatan_kepala_daerah VARCHAR(100) NULL,
    ibukota VARCHAR(150) NULL,
    alamat TEXT NULL,
    website VARCHAR(255) NULL,
    email VARCHAR(150) NULL,
    telepon VARCHAR(50) NULL,
    is_aktif TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_pemda_aktif CHECK (is_aktif IN (0, 1)),
    FOREIGN KEY (parent_id) REFERENCES pemda(id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE unit_organisasi (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    pemda_id BIGINT UNSIGNED NOT NULL,
    parent_id BIGINT UNSIGNED NULL,
    kode_unit VARCHAR(50) NOT NULL,
    nama VARCHAR(255) NOT NULL,
    singkatan VARCHAR(80) NULL,
    jenis_unit ENUM('PEMDA','SEKRETARIAT_DAERAH','INSPEKTORAT','DINAS','BADAN','KECAMATAN','KELURAHAN','UPTD','BIDANG','BAGIAN','SUBBAGIAN','SEKSI','LAINNYA') NOT NULL,
    level_unit ENUM('PEMDA','OPD','UNIT_KERJA','SUB_UNIT') NOT NULL,
    urusan_id BIGINT UNSIGNED NULL,
    alamat TEXT NULL,
    email VARCHAR(150) NULL,
    telepon VARCHAR(50) NULL,
    is_aktif TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_unit_pemda_kode (pemda_id, kode_unit),
    INDEX idx_unit_parent (parent_id),
    CONSTRAINT chk_unit_aktif CHECK (is_aktif IN (0, 1)),
    FOREIGN KEY (pemda_id) REFERENCES pemda(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (parent_id) REFERENCES unit_organisasi(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (urusan_id) REFERENCES ref_urusan(id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE jabatan (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    unit_id BIGINT UNSIGNED NOT NULL,
    parent_id BIGINT UNSIGNED NULL,
    nama VARCHAR(200) NOT NULL,
    jenis_jabatan ENUM('KEPALA_DAERAH','SEKDA','KEPALA_OPD','ADMINISTRATOR','PENGAWAS','FUNGSIONAL','PELAKSANA','LAINNYA') NOT NULL,
    eselon VARCHAR(20) NULL,
    kelas_jabatan VARCHAR(20) NULL,
    is_aktif TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_jabatan_aktif CHECK (is_aktif IN (0, 1)),
    FOREIGN KEY (unit_id) REFERENCES unit_organisasi(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (parent_id) REFERENCES jabatan(id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE pegawai (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    pemda_id BIGINT UNSIGNED NOT NULL,
    unit_id BIGINT UNSIGNED NULL,
    jabatan_id BIGINT UNSIGNED NULL,
    nip VARCHAR(30) NULL UNIQUE,
    nik VARCHAR(30) NULL,
    nama VARCHAR(200) NOT NULL,
    gelar_depan VARCHAR(50) NULL,
    gelar_belakang VARCHAR(80) NULL,
    email VARCHAR(150) NULL,
    telepon VARCHAR(50) NULL,
    status_pegawai ENUM('PNS','PPPK','NON_ASN','LAINNYA') NOT NULL DEFAULT 'PNS',
    is_aktif TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_pegawai_aktif CHECK (is_aktif IN (0, 1)),
    FOREIGN KEY (pemda_id) REFERENCES pemda(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (unit_id) REFERENCES unit_organisasi(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (jabatan_id) REFERENCES jabatan(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE app_user (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    pegawai_id BIGINT UNSIGNED NULL,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nama VARCHAR(200) NOT NULL,
    status ENUM('AKTIF','NONAKTIF','TERKUNCI') NOT NULL DEFAULT 'AKTIF',
    last_login_at DATETIME NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (pegawai_id) REFERENCES pegawai(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE app_role (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    kode VARCHAR(50) NOT NULL UNIQUE,
    nama VARCHAR(120) NOT NULL,
    deskripsi TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE app_permission (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    kode VARCHAR(100) NOT NULL UNIQUE,
    nama VARCHAR(150) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE app_user_role (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    role_id BIGINT UNSIGNED NOT NULL,
    unit_id BIGINT UNSIGNED NULL,
    unit_scope_id BIGINT UNSIGNED GENERATED ALWAYS AS (COALESCE(unit_id, 0)) STORED,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_app_user_role_scope (user_id, role_id, unit_scope_id),
    INDEX idx_app_user_role_role (role_id),
    INDEX idx_app_user_role_unit (unit_id),
    FOREIGN KEY (user_id) REFERENCES app_user(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES app_role(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (unit_id) REFERENCES unit_organisasi(id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE app_role_permission (
    role_id BIGINT UNSIGNED NOT NULL,
    permission_id BIGINT UNSIGNED NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES app_role(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES app_permission(id) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE dokumen (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    pemda_id BIGINT UNSIGNED NOT NULL,
    unit_id BIGINT UNSIGNED NULL,
    jenis_dokumen_id BIGINT UNSIGNED NOT NULL,
    tahun SMALLINT NULL,
    periode_awal SMALLINT NULL,
    periode_akhir SMALLINT NULL,
    nomor_dokumen VARCHAR(100) NULL,
    judul VARCHAR(255) NOT NULL,
    ringkasan TEXT NULL,
    status ENUM('DRAFT','DIAJUKAN','DIVERIFIKASI','DITETAPKAN','DIREVISI','ARSIP') NOT NULL DEFAULT 'DRAFT',
    tanggal_dokumen DATE NULL,
    tanggal_penetapan DATE NULL,
    created_by BIGINT UNSIGNED NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_dokumen_scope (pemda_id, unit_id, tahun, status),
    INDEX idx_dokumen_jenis_status (jenis_dokumen_id, status),
    INDEX idx_dokumen_created_by (created_by, created_at),
    CONSTRAINT chk_dokumen_tahun CHECK (tahun IS NULL OR tahun BETWEEN 1900 AND 2200),
    CONSTRAINT chk_dokumen_periode CHECK (
        periode_awal IS NULL OR periode_akhir IS NULL OR periode_awal <= periode_akhir
    ),
    FOREIGN KEY (pemda_id) REFERENCES pemda(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (unit_id) REFERENCES unit_organisasi(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (jenis_dokumen_id) REFERENCES ref_dokumen_jenis(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (created_by) REFERENCES app_user(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE dokumen_versi (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    dokumen_id BIGINT UNSIGNED NOT NULL,
    versi INT NOT NULL DEFAULT 1,
    nama_file VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    mime_type VARCHAR(120) NULL,
    ukuran_byte BIGINT UNSIGNED NULL,
    sha256 CHAR(64) NULL,
    catatan_perubahan TEXT NULL,
    uploaded_by BIGINT UNSIGNED NULL,
    uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_dokumen_versi (dokumen_id, versi),
    INDEX idx_dokumen_versi_uploaded (uploaded_by, uploaded_at),
    INDEX idx_dokumen_versi_sha256 (sha256),
    CONSTRAINT chk_dokumen_versi_versi CHECK (versi > 0),
    CONSTRAINT chk_dokumen_versi_ukuran CHECK (ukuran_byte IS NULL OR ukuran_byte >= 0),
    FOREIGN KEY (dokumen_id) REFERENCES dokumen(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES app_user(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE dokumen_bukti (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    dokumen_id BIGINT UNSIGNED NULL,
    pemda_id BIGINT UNSIGNED NOT NULL,
    unit_id BIGINT UNSIGNED NULL,
    tahun SMALLINT NULL,
    judul VARCHAR(255) NOT NULL,
    uraian TEXT NULL,
    nama_file VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    mime_type VARCHAR(120) NULL,
    ukuran_byte BIGINT UNSIGNED NULL,
    sha256 CHAR(64) NULL,
    uploaded_by BIGINT UNSIGNED NULL,
    uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_bukti_scope (pemda_id, unit_id, tahun),
    INDEX idx_bukti_uploaded (uploaded_by, uploaded_at),
    INDEX idx_bukti_sha256 (sha256),
    CONSTRAINT chk_dokumen_bukti_tahun CHECK (tahun IS NULL OR tahun BETWEEN 1900 AND 2200),
    CONSTRAINT chk_dokumen_bukti_ukuran CHECK (ukuran_byte IS NULL OR ukuran_byte >= 0),
    FOREIGN KEY (dokumen_id) REFERENCES dokumen(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (pemda_id) REFERENCES pemda(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (unit_id) REFERENCES unit_organisasi(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (uploaded_by) REFERENCES app_user(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE dokumen_relasi (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    dokumen_id BIGINT UNSIGNED NOT NULL,
    related_dokumen_id BIGINT UNSIGNED NOT NULL,
    jenis_relasi ENUM('TURUNAN','RUJUKAN','REVISI','BUKTI','LAMPIRAN','LAINNYA') NOT NULL,
    catatan TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_dokumen_relasi (dokumen_id, related_dokumen_id, jenis_relasi),
    INDEX idx_dokumen_relasi_related (related_dokumen_id, jenis_relasi),
    CONSTRAINT chk_dokumen_relasi_not_self CHECK (dokumen_id <> related_dokumen_id),
    FOREIGN KEY (dokumen_id) REFERENCES dokumen(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (related_dokumen_id) REFERENCES dokumen(id) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE rpjmd_dokumen (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    pemda_id BIGINT UNSIGNED NOT NULL,
    dokumen_id BIGINT UNSIGNED NOT NULL,
    tahun_awal SMALLINT NOT NULL,
    tahun_akhir SMALLINT NOT NULL,
    visi TEXT NOT NULL,
    misi_ringkas TEXT NULL,
    status ENUM('DRAFT','RANCANGAN','PERDA','PERKADA','PERUBAHAN','ARSIP') NOT NULL DEFAULT 'DRAFT',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_rpjmd_scope (pemda_id, tahun_awal, tahun_akhir, status),
    CONSTRAINT chk_rpjmd_tahun CHECK (tahun_awal BETWEEN 1900 AND 2200 AND tahun_akhir >= tahun_awal),
    FOREIGN KEY (pemda_id) REFERENCES pemda(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (dokumen_id) REFERENCES dokumen(id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE renstra_dokumen (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    pemda_id BIGINT UNSIGNED NOT NULL,
    unit_id BIGINT UNSIGNED NOT NULL,
    dokumen_id BIGINT UNSIGNED NOT NULL,
    rpjmd_id BIGINT UNSIGNED NULL,
    tahun_awal SMALLINT NOT NULL,
    tahun_akhir SMALLINT NOT NULL,
    isu_strategis TEXT NULL,
    status ENUM('DRAFT','DIAJUKAN','DIVERIFIKASI','DITETAPKAN','PERUBAHAN','ARSIP') NOT NULL DEFAULT 'DRAFT',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_renstra_scope (pemda_id, unit_id, tahun_awal, tahun_akhir, status),
    INDEX idx_renstra_rpjmd (rpjmd_id),
    CONSTRAINT chk_renstra_tahun CHECK (tahun_awal BETWEEN 1900 AND 2200 AND tahun_akhir >= tahun_awal),
    FOREIGN KEY (pemda_id) REFERENCES pemda(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (unit_id) REFERENCES unit_organisasi(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (dokumen_id) REFERENCES dokumen(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (rpjmd_id) REFERENCES rpjmd_dokumen(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE rkpd_dokumen (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    pemda_id BIGINT UNSIGNED NOT NULL,
    dokumen_id BIGINT UNSIGNED NOT NULL,
    tahun SMALLINT NOT NULL,
    tema_pembangunan TEXT NULL,
    prioritas_daerah TEXT NULL,
    status ENUM('DRAFT','RANCANGAN','PERKADA','PERUBAHAN','ARSIP') NOT NULL DEFAULT 'DRAFT',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_rkpd_scope (pemda_id, tahun, status),
    CONSTRAINT chk_rkpd_tahun CHECK (tahun BETWEEN 1900 AND 2200),
    FOREIGN KEY (pemda_id) REFERENCES pemda(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (dokumen_id) REFERENCES dokumen(id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE renja_dokumen (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    pemda_id BIGINT UNSIGNED NOT NULL,
    unit_id BIGINT UNSIGNED NOT NULL,
    dokumen_id BIGINT UNSIGNED NOT NULL,
    renstra_id BIGINT UNSIGNED NULL,
    rkpd_id BIGINT UNSIGNED NULL,
    tahun SMALLINT NOT NULL,
    status ENUM('DRAFT','DIAJUKAN','DIVERIFIKASI','DITETAPKAN','PERUBAHAN','ARSIP') NOT NULL DEFAULT 'DRAFT',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_renja_scope (pemda_id, unit_id, tahun, status),
    INDEX idx_renja_renstra (renstra_id),
    INDEX idx_renja_rkpd (rkpd_id),
    CONSTRAINT chk_renja_tahun CHECK (tahun BETWEEN 1900 AND 2200),
    FOREIGN KEY (pemda_id) REFERENCES pemda(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (unit_id) REFERENCES unit_organisasi(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (dokumen_id) REFERENCES dokumen(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (renstra_id) REFERENCES renstra_dokumen(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (rkpd_id) REFERENCES rkpd_dokumen(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE sakip_kinerja_node (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    pemda_id BIGINT UNSIGNED NOT NULL,
    unit_id BIGINT UNSIGNED NULL,
    parent_id BIGINT UNSIGNED NULL,
    kode VARCHAR(100) NULL,
    jenis_node ENUM(
        'VISI',
        'MISI',
        'TUJUAN_DAERAH',
        'SASARAN_DAERAH',
        'STRATEGI',
        'ARAH_KEBIJAKAN',
        'TUJUAN_OPD',
        'SASARAN_OPD',
        'PROGRAM',
        'KEGIATAN',
        'SUB_KEGIATAN',
        'OUTPUT',
        'OUTCOME',
        'AKTIVITAS',
        'KINERJA_INDIVIDU',
        'LAINNYA'
    ) NOT NULL,
    uraian TEXT NOT NULL,
    level_kinerja ENUM('PEMDA','OPD','UNIT','INDIVIDU') NOT NULL,
    tahun_awal SMALLINT NOT NULL,
    tahun_akhir SMALLINT NOT NULL,
    rpjmd_id BIGINT UNSIGNED NULL,
    renstra_id BIGINT UNSIGNED NULL,
    rkpd_id BIGINT UNSIGNED NULL,
    renja_id BIGINT UNSIGNED NULL,
    ref_program_id BIGINT UNSIGNED NULL,
    ref_kegiatan_id BIGINT UNSIGNED NULL,
    ref_sub_kegiatan_id BIGINT UNSIGNED NULL,
    urutan INT NOT NULL DEFAULT 0,
    is_prioritas TINYINT(1) NOT NULL DEFAULT 0,
    status ENUM('DRAFT','AKTIF','NONAKTIF','ARSIP') NOT NULL DEFAULT 'DRAFT',
    created_by BIGINT UNSIGNED NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_node_parent (parent_id),
    INDEX idx_node_unit_tahun (unit_id, tahun_awal, tahun_akhir),
    INDEX idx_node_jenis (jenis_node),
    INDEX idx_node_pemda_status_jenis (pemda_id, status, jenis_node),
    INDEX idx_node_pemda_tahun_status (pemda_id, tahun_awal, tahun_akhir, status),
    INDEX idx_node_program (ref_program_id),
    INDEX idx_node_kegiatan (ref_kegiatan_id),
    INDEX idx_node_sub_kegiatan (ref_sub_kegiatan_id),
    CONSTRAINT chk_node_tahun CHECK (tahun_awal BETWEEN 1900 AND 2200 AND tahun_akhir >= tahun_awal),
    CONSTRAINT chk_node_boolean CHECK (is_prioritas IN (0, 1)),
    FOREIGN KEY (pemda_id) REFERENCES pemda(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (unit_id) REFERENCES unit_organisasi(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (parent_id) REFERENCES sakip_kinerja_node(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (rpjmd_id) REFERENCES rpjmd_dokumen(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (renstra_id) REFERENCES renstra_dokumen(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (rkpd_id) REFERENCES rkpd_dokumen(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (renja_id) REFERENCES renja_dokumen(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (ref_program_id) REFERENCES ref_program(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (ref_kegiatan_id) REFERENCES ref_kegiatan(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (ref_sub_kegiatan_id) REFERENCES ref_sub_kegiatan(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (created_by) REFERENCES app_user(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE sakip_cascading_relasi (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    parent_node_id BIGINT UNSIGNED NOT NULL,
    child_node_id BIGINT UNSIGNED NOT NULL,
    jenis_relasi ENUM('TURUNAN_LANGSUNG','KONTRIBUSI','DUKUNGAN','MANDAT','CROSS_CUTTING') NOT NULL,
    bobot_kontribusi DECIMAL(6,2) NULL,
    logika_kontribusi TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_cascade (parent_node_id, child_node_id, jenis_relasi),
    CONSTRAINT chk_cascade_not_self CHECK (parent_node_id <> child_node_id),
    CONSTRAINT chk_cascade_bobot CHECK (bobot_kontribusi IS NULL OR bobot_kontribusi BETWEEN 0 AND 100),
    FOREIGN KEY (parent_node_id) REFERENCES sakip_kinerja_node(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (child_node_id) REFERENCES sakip_kinerja_node(id) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE sakip_crosscutting_relasi (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    node_id BIGINT UNSIGNED NOT NULL,
    unit_pemilik_id BIGINT UNSIGNED NOT NULL,
    unit_pendukung_id BIGINT UNSIGNED NOT NULL,
    peran_pendukung VARCHAR(255) NOT NULL,
    output_dukungan TEXT NULL,
    tahun SMALLINT NOT NULL,
    status ENUM('DRAFT','DISEPAKATI','BERJALAN','SELESAI','BATAL') NOT NULL DEFAULT 'DRAFT',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_crosscutting (node_id, unit_pemilik_id, unit_pendukung_id, tahun),
    INDEX idx_crosscutting_pemilik (unit_pemilik_id, tahun, status),
    INDEX idx_crosscutting_pendukung (unit_pendukung_id, tahun, status),
    CONSTRAINT chk_crosscutting_tahun CHECK (tahun BETWEEN 1900 AND 2200),
    CONSTRAINT chk_crosscutting_unit CHECK (unit_pemilik_id <> unit_pendukung_id),
    FOREIGN KEY (node_id) REFERENCES sakip_kinerja_node(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (unit_pemilik_id) REFERENCES unit_organisasi(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (unit_pendukung_id) REFERENCES unit_organisasi(id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE sakip_indikator (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    node_id BIGINT UNSIGNED NOT NULL,
    kode VARCHAR(100) NULL,
    nama VARCHAR(255) NOT NULL,
    definisi_operasional TEXT NULL,
    formula TEXT NULL,
    satuan_id BIGINT UNSIGNED NULL,
    jenis_indikator ENUM('INPUT','PROSES','OUTPUT','OUTCOME','IMPACT','IKU','IKK','IKD','IKP','LAINNYA') NOT NULL,
    arah_capaian ENUM('MAKSIMAL','MINIMAL','STABIL','SEMUA_SEMAKIN_BAIK') NOT NULL DEFAULT 'MAKSIMAL',
    sumber_data TEXT NULL,
    metode_pengukuran TEXT NULL,
    frekuensi_pengukuran ENUM('BULANAN','TRIWULANAN','SEMESTERAN','TAHUNAN','LIMA_TAHUNAN') NOT NULL DEFAULT 'TAHUNAN',
    penanggung_jawab_unit_id BIGINT UNSIGNED NULL,
    penanggung_jawab_pegawai_id BIGINT UNSIGNED NULL,
    is_iku TINYINT(1) NOT NULL DEFAULT 0,
    is_pk TINYINT(1) NOT NULL DEFAULT 0,
    is_publikasi TINYINT(1) NOT NULL DEFAULT 0,
    status ENUM('DRAFT','AKTIF','NONAKTIF','ARSIP') NOT NULL DEFAULT 'DRAFT',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_indikator_node (node_id),
    INDEX idx_indikator_status_flags (status, is_iku, is_pk),
    INDEX idx_indikator_unit_status (penanggung_jawab_unit_id, status),
    UNIQUE KEY uq_indikator_id_node (id, node_id),
    CONSTRAINT chk_indikator_boolean CHECK (
        is_iku IN (0, 1) AND is_pk IN (0, 1) AND is_publikasi IN (0, 1)
    ),
    FOREIGN KEY (node_id) REFERENCES sakip_kinerja_node(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (satuan_id) REFERENCES ref_satuan(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (penanggung_jawab_unit_id) REFERENCES unit_organisasi(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (penanggung_jawab_pegawai_id) REFERENCES pegawai(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE sakip_target (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    indikator_id BIGINT UNSIGNED NOT NULL,
    tahun SMALLINT NOT NULL,
    periode ENUM('TAHUNAN','SEMESTER_1','SEMESTER_2','TRIWULAN_1','TRIWULAN_2','TRIWULAN_3','TRIWULAN_4','BULAN_1','BULAN_2','BULAN_3','BULAN_4','BULAN_5','BULAN_6','BULAN_7','BULAN_8','BULAN_9','BULAN_10','BULAN_11','BULAN_12') NOT NULL DEFAULT 'TAHUNAN',
    target_angka DECIMAL(20,4) NULL,
    target_teks VARCHAR(255) NULL,
    target_min DECIMAL(20,4) NULL,
    target_max DECIMAL(20,4) NULL,
    baseline DECIMAL(20,4) NULL,
    pagu_indikatif DECIMAL(18,2) NULL,
    catatan TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_target (indikator_id, tahun, periode),
    UNIQUE KEY uq_target_id_indikator (id, indikator_id),
    INDEX idx_target_tahun_periode (tahun, periode),
    CONSTRAINT chk_target_tahun CHECK (tahun BETWEEN 1900 AND 2200),
    CONSTRAINT chk_target_range CHECK (target_min IS NULL OR target_max IS NULL OR target_min <= target_max),
    CONSTRAINT chk_target_pagu CHECK (pagu_indikatif IS NULL OR pagu_indikatif >= 0),
    FOREIGN KEY (indikator_id) REFERENCES sakip_indikator(id) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE sakip_realisasi (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    indikator_id BIGINT UNSIGNED NOT NULL,
    tahun SMALLINT NOT NULL,
    periode ENUM('TAHUNAN','SEMESTER_1','SEMESTER_2','TRIWULAN_1','TRIWULAN_2','TRIWULAN_3','TRIWULAN_4','BULAN_1','BULAN_2','BULAN_3','BULAN_4','BULAN_5','BULAN_6','BULAN_7','BULAN_8','BULAN_9','BULAN_10','BULAN_11','BULAN_12') NOT NULL DEFAULT 'TAHUNAN',
    realisasi_angka DECIMAL(20,4) NULL,
    realisasi_teks VARCHAR(255) NULL,
    tanggal_input DATE NOT NULL,
    sumber_data TEXT NULL,
    kendala TEXT NULL,
    upaya_perbaikan TEXT NULL,
    status_validasi ENUM('DRAFT','DIAJUKAN','VALID','DITOLAK','REVISI') NOT NULL DEFAULT 'DRAFT',
    validator_user_id BIGINT UNSIGNED NULL,
    validated_at DATETIME NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_realisasi (indikator_id, tahun, periode),
    UNIQUE KEY uq_realisasi_id_indikator (id, indikator_id),
    INDEX idx_realisasi_tahun_periode (tahun, periode),
    INDEX idx_realisasi_validasi (status_validasi, validator_user_id, validated_at),
    CONSTRAINT chk_realisasi_tahun CHECK (tahun BETWEEN 1900 AND 2200),
    FOREIGN KEY (indikator_id) REFERENCES sakip_indikator(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (validator_user_id) REFERENCES app_user(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE sakip_capaian (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    indikator_id BIGINT UNSIGNED NOT NULL,
    target_id BIGINT UNSIGNED NOT NULL,
    realisasi_id BIGINT UNSIGNED NOT NULL,
    capaian_persen DECIMAL(8,2) NULL,
    predikat VARCHAR(50) NULL,
    analisis_capaian TEXT NULL,
    analisis_efisiensi TEXT NULL,
    faktor_pendorong TEXT NULL,
    faktor_penghambat TEXT NULL,
    rekomendasi_perbaikan TEXT NULL,
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_capaian (indikator_id, target_id, realisasi_id),
    INDEX idx_capaian_target_indikator (target_id, indikator_id),
    INDEX idx_capaian_realisasi_indikator (realisasi_id, indikator_id),
    CONSTRAINT chk_capaian_persen CHECK (capaian_persen IS NULL OR capaian_persen >= 0),
    FOREIGN KEY (indikator_id) REFERENCES sakip_indikator(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (target_id, indikator_id) REFERENCES sakip_target(id, indikator_id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (realisasi_id, indikator_id) REFERENCES sakip_realisasi(id, indikator_id) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE anggaran_pagu (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    pemda_id BIGINT UNSIGNED NOT NULL,
    unit_id BIGINT UNSIGNED NOT NULL,
    node_id BIGINT UNSIGNED NULL,
    tahun SMALLINT NOT NULL,
    jenis_pagu ENUM('INDIKATIF','RKPD','KUA_PPAS','RKA','DPA','DPPA','PERUBAHAN') NOT NULL,
    belanja_operasi DECIMAL(18,2) NOT NULL DEFAULT 0,
    belanja_modal DECIMAL(18,2) NOT NULL DEFAULT 0,
    belanja_tidak_terduga DECIMAL(18,2) NOT NULL DEFAULT 0,
    belanja_transfer DECIMAL(18,2) NOT NULL DEFAULT 0,
    total_pagu DECIMAL(18,2) NOT NULL DEFAULT 0,
    sumber_dana VARCHAR(150) NULL,
    catatan TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_anggaran_pagu_scope (pemda_id, unit_id, tahun, jenis_pagu),
    INDEX idx_anggaran_pagu_node (node_id, tahun),
    CONSTRAINT chk_anggaran_pagu_tahun CHECK (tahun BETWEEN 1900 AND 2200),
    CONSTRAINT chk_anggaran_pagu_nonnegative CHECK (
        belanja_operasi >= 0
        AND belanja_modal >= 0
        AND belanja_tidak_terduga >= 0
        AND belanja_transfer >= 0
        AND total_pagu >= 0
    ),
    FOREIGN KEY (pemda_id) REFERENCES pemda(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (unit_id) REFERENCES unit_organisasi(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (node_id) REFERENCES sakip_kinerja_node(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE anggaran_realisasi (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    pagu_id BIGINT UNSIGNED NOT NULL,
    tahun SMALLINT NOT NULL,
    periode ENUM('TAHUNAN','TRIWULAN_1','TRIWULAN_2','TRIWULAN_3','TRIWULAN_4','BULAN_1','BULAN_2','BULAN_3','BULAN_4','BULAN_5','BULAN_6','BULAN_7','BULAN_8','BULAN_9','BULAN_10','BULAN_11','BULAN_12') NOT NULL,
    realisasi_keuangan DECIMAL(18,2) NOT NULL DEFAULT 0,
    realisasi_fisik DECIMAL(6,2) NULL,
    catatan TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_anggaran_realisasi (pagu_id, tahun, periode),
    CONSTRAINT chk_anggaran_realisasi_tahun CHECK (tahun BETWEEN 1900 AND 2200),
    CONSTRAINT chk_anggaran_realisasi_keuangan CHECK (realisasi_keuangan >= 0),
    CONSTRAINT chk_anggaran_realisasi_fisik CHECK (realisasi_fisik IS NULL OR realisasi_fisik BETWEEN 0 AND 100),
    FOREIGN KEY (pagu_id) REFERENCES anggaran_pagu(id) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE rencana_aksi (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    pemda_id BIGINT UNSIGNED NOT NULL,
    unit_id BIGINT UNSIGNED NOT NULL,
    node_id BIGINT UNSIGNED NOT NULL,
    indikator_id BIGINT UNSIGNED NULL,
    tahun SMALLINT NOT NULL,
    nama_aksi VARCHAR(255) NOT NULL,
    uraian TEXT NULL,
    output_aksi TEXT NULL,
    penanggung_jawab_pegawai_id BIGINT UNSIGNED NULL,
    status ENUM('DRAFT','AKTIF','SELESAI','TERLAMBAT','BATAL') NOT NULL DEFAULT 'DRAFT',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_rencana_aksi_scope (pemda_id, unit_id, tahun, status),
    INDEX idx_rencana_aksi_node (node_id, tahun, status),
    INDEX idx_rencana_aksi_indikator (indikator_id, tahun),
    INDEX idx_rencana_aksi_pj (penanggung_jawab_pegawai_id, tahun, status),
    CONSTRAINT chk_rencana_aksi_tahun CHECK (tahun BETWEEN 1900 AND 2200),
    FOREIGN KEY (pemda_id) REFERENCES pemda(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (unit_id) REFERENCES unit_organisasi(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (node_id) REFERENCES sakip_kinerja_node(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (indikator_id) REFERENCES sakip_indikator(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (penanggung_jawab_pegawai_id) REFERENCES pegawai(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE rencana_aksi_detail (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    rencana_aksi_id BIGINT UNSIGNED NOT NULL,
    periode ENUM('TRIWULAN_1','TRIWULAN_2','TRIWULAN_3','TRIWULAN_4','BULAN_1','BULAN_2','BULAN_3','BULAN_4','BULAN_5','BULAN_6','BULAN_7','BULAN_8','BULAN_9','BULAN_10','BULAN_11','BULAN_12') NOT NULL,
    target_output TEXT NULL,
    realisasi_output TEXT NULL,
    target_fisik DECIMAL(6,2) NULL,
    realisasi_fisik DECIMAL(6,2) NULL,
    target_keuangan DECIMAL(18,2) NULL,
    realisasi_keuangan DECIMAL(18,2) NULL,
    kendala TEXT NULL,
    tindak_lanjut TEXT NULL,
    status ENUM('BELUM_MULAI','BERJALAN','SELESAI','TERLAMBAT','BATAL') NOT NULL DEFAULT 'BELUM_MULAI',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_aksi_detail (rencana_aksi_id, periode),
    INDEX idx_aksi_detail_status (status),
    CONSTRAINT chk_aksi_detail_fisik CHECK (
        (target_fisik IS NULL OR target_fisik BETWEEN 0 AND 100)
        AND (realisasi_fisik IS NULL OR realisasi_fisik BETWEEN 0 AND 100)
    ),
    CONSTRAINT chk_aksi_detail_keuangan CHECK (
        (target_keuangan IS NULL OR target_keuangan >= 0)
        AND (realisasi_keuangan IS NULL OR realisasi_keuangan >= 0)
    ),
    FOREIGN KEY (rencana_aksi_id) REFERENCES rencana_aksi(id) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE pk_dokumen (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    pemda_id BIGINT UNSIGNED NOT NULL,
    unit_id BIGINT UNSIGNED NOT NULL,
    dokumen_id BIGINT UNSIGNED NOT NULL,
    tahun SMALLINT NOT NULL,
    nomor_pk VARCHAR(100) NULL,
    tanggal_pk DATE NULL,
    status ENUM('DRAFT','DIAJUKAN','DITANDATANGANI','DIREVISI','ARSIP') NOT NULL DEFAULT 'DRAFT',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_pk_scope (pemda_id, unit_id, tahun, status),
    CONSTRAINT chk_pk_tahun CHECK (tahun BETWEEN 1900 AND 2200),
    FOREIGN KEY (pemda_id) REFERENCES pemda(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (unit_id) REFERENCES unit_organisasi(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (dokumen_id) REFERENCES dokumen(id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE pk_pihak (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    pk_id BIGINT UNSIGNED NOT NULL,
    pihak ENUM('PIHAK_PERTAMA','PIHAK_KEDUA') NOT NULL,
    pegawai_id BIGINT UNSIGNED NULL,
    nama VARCHAR(200) NOT NULL,
    nip VARCHAR(30) NULL,
    jabatan VARCHAR(200) NOT NULL,
    unit VARCHAR(200) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_pk_pihak (pk_id, pihak),
    FOREIGN KEY (pk_id) REFERENCES pk_dokumen(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (pegawai_id) REFERENCES pegawai(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE pk_detail (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    pk_id BIGINT UNSIGNED NOT NULL,
    node_id BIGINT UNSIGNED NOT NULL,
    indikator_id BIGINT UNSIGNED NOT NULL,
    target_id BIGINT UNSIGNED NOT NULL,
    urutan INT NOT NULL DEFAULT 0,
    keterangan TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_pk_indikator (pk_id, indikator_id, target_id),
    INDEX idx_pk_detail_target_indikator (target_id, indikator_id),
    FOREIGN KEY (pk_id) REFERENCES pk_dokumen(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (node_id) REFERENCES sakip_kinerja_node(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (indikator_id) REFERENCES sakip_indikator(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (target_id, indikator_id) REFERENCES sakip_target(id, indikator_id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE lkjip_dokumen (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    pemda_id BIGINT UNSIGNED NOT NULL,
    unit_id BIGINT UNSIGNED NULL,
    dokumen_id BIGINT UNSIGNED NOT NULL,
    tahun SMALLINT NOT NULL,
    level_laporan ENUM('PEMDA','OPD','UNIT') NOT NULL,
    status ENUM('DRAFT','DIAJUKAN','DIREVIU','FINAL','DIPUBLIKASIKAN','ARSIP') NOT NULL DEFAULT 'DRAFT',
    tanggal_laporan DATE NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_lkjip_scope (pemda_id, unit_id, tahun, status),
    INDEX idx_lkjip_level_status (level_laporan, status),
    CONSTRAINT chk_lkjip_tahun CHECK (tahun BETWEEN 1900 AND 2200),
    FOREIGN KEY (pemda_id) REFERENCES pemda(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (unit_id) REFERENCES unit_organisasi(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (dokumen_id) REFERENCES dokumen(id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE lkjip_bab (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    lkjip_id BIGINT UNSIGNED NOT NULL,
    kode_bab VARCHAR(30) NOT NULL,
    judul VARCHAR(255) NOT NULL,
    isi LONGTEXT NULL,
    urutan INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_lkjip_bab (lkjip_id, kode_bab),
    FOREIGN KEY (lkjip_id) REFERENCES lkjip_dokumen(id) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE lkjip_capaian (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    lkjip_id BIGINT UNSIGNED NOT NULL,
    node_id BIGINT UNSIGNED NOT NULL,
    indikator_id BIGINT UNSIGNED NOT NULL,
    target_id BIGINT UNSIGNED NULL,
    realisasi_id BIGINT UNSIGNED NULL,
    capaian_id BIGINT UNSIGNED NULL,
    narasi_analisis TEXT NULL,
    narasi_efisiensi TEXT NULL,
    rekomendasi TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_lkjip_capaian_indikator (lkjip_id, indikator_id),
    INDEX idx_lkjip_capaian_target_indikator (target_id, indikator_id),
    INDEX idx_lkjip_capaian_realisasi_indikator (realisasi_id, indikator_id),
    FOREIGN KEY (lkjip_id) REFERENCES lkjip_dokumen(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (node_id) REFERENCES sakip_kinerja_node(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (indikator_id) REFERENCES sakip_indikator(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (target_id, indikator_id) REFERENCES sakip_target(id, indikator_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (realisasi_id, indikator_id) REFERENCES sakip_realisasi(id, indikator_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (capaian_id) REFERENCES sakip_capaian(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE lkjip_reviu (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    lkjip_id BIGINT UNSIGNED NOT NULL,
    reviewer_user_id BIGINT UNSIGNED NULL,
    tanggal_reviu DATE NULL,
    hasil_reviu ENUM('LAYAK','LAYAK_DENGAN_CATATAN','PERLU_REVISI','DITOLAK') NOT NULL,
    catatan_umum TEXT NULL,
    catatan_perbaikan TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (lkjip_id) REFERENCES lkjip_dokumen(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (reviewer_user_id) REFERENCES app_user(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE lke_template (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    kode VARCHAR(50) NOT NULL UNIQUE,
    nama VARCHAR(255) NOT NULL,
    tahun_berlaku SMALLINT NOT NULL,
    regulasi_id BIGINT UNSIGNED NULL,
    total_bobot DECIMAL(6,2) NOT NULL DEFAULT 100.00,
    is_aktif TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_lke_template_tahun_aktif (tahun_berlaku, is_aktif),
    CONSTRAINT chk_lke_template_tahun CHECK (tahun_berlaku BETWEEN 1900 AND 2200),
    CONSTRAINT chk_lke_template_bobot CHECK (total_bobot > 0),
    CONSTRAINT chk_lke_template_aktif CHECK (is_aktif IN (0, 1)),
    FOREIGN KEY (regulasi_id) REFERENCES ref_regulasi(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE lke_komponen (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    template_id BIGINT UNSIGNED NOT NULL,
    kode VARCHAR(50) NOT NULL,
    nama VARCHAR(255) NOT NULL,
    bobot DECIMAL(6,2) NOT NULL,
    urutan INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_lke_komponen (template_id, kode),
    CONSTRAINT chk_lke_komponen_bobot CHECK (bobot >= 0),
    FOREIGN KEY (template_id) REFERENCES lke_template(id) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE lke_subkomponen (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    komponen_id BIGINT UNSIGNED NOT NULL,
    kode VARCHAR(50) NOT NULL,
    nama VARCHAR(255) NOT NULL,
    bobot DECIMAL(6,2) NOT NULL,
    urutan INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_lke_subkomponen (komponen_id, kode),
    CONSTRAINT chk_lke_subkomponen_bobot CHECK (bobot >= 0),
    FOREIGN KEY (komponen_id) REFERENCES lke_komponen(id) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE lke_kriteria (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    subkomponen_id BIGINT UNSIGNED NOT NULL,
    kode VARCHAR(50) NOT NULL,
    pertanyaan TEXT NOT NULL,
    bobot DECIMAL(6,2) NOT NULL,
    tipe_jawaban ENUM('YA_TIDAK','SKALA_0_1','SKALA_0_5','NILAI','TEKS') NOT NULL DEFAULT 'SKALA_0_1',
    membutuhkan_bukti TINYINT(1) NOT NULL DEFAULT 1,
    urutan INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_lke_kriteria (subkomponen_id, kode),
    CONSTRAINT chk_lke_kriteria_bobot CHECK (bobot >= 0),
    CONSTRAINT chk_lke_kriteria_bukti CHECK (membutuhkan_bukti IN (0, 1)),
    FOREIGN KEY (subkomponen_id) REFERENCES lke_subkomponen(id) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE evaluasi_akip (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    pemda_id BIGINT UNSIGNED NOT NULL,
    tahun SMALLINT NOT NULL,
    template_id BIGINT UNSIGNED NOT NULL,
    level_evaluasi ENUM('PEMDA','OPD','UNIT') NOT NULL,
    jenis_evaluasi ENUM('MANDIRI','INTERNAL_INSPEKTORAT','EKSTERNAL','REVIU') NOT NULL,
    tanggal_mulai DATE NULL,
    tanggal_selesai DATE NULL,
    status ENUM('DRAFT','BERJALAN','SELESAI','DIKUNCI','ARSIP') NOT NULL DEFAULT 'DRAFT',
    ketua_tim_user_id BIGINT UNSIGNED NULL,
    catatan_umum TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_evaluasi_akip_scope (pemda_id, tahun, level_evaluasi, status),
    INDEX idx_evaluasi_akip_template (template_id, tahun),
    INDEX idx_evaluasi_akip_ketua (ketua_tim_user_id, tahun, status),
    CONSTRAINT chk_evaluasi_akip_tahun CHECK (tahun BETWEEN 1900 AND 2200),
    CONSTRAINT chk_evaluasi_akip_tanggal CHECK (
        tanggal_mulai IS NULL OR tanggal_selesai IS NULL OR tanggal_selesai >= tanggal_mulai
    ),
    FOREIGN KEY (pemda_id) REFERENCES pemda(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (template_id) REFERENCES lke_template(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (ketua_tim_user_id) REFERENCES app_user(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE evaluasi_unit (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    evaluasi_id BIGINT UNSIGNED NOT NULL,
    unit_id BIGINT UNSIGNED NULL,
    nilai_total DECIMAL(6,2) NULL,
    predikat_id BIGINT UNSIGNED NULL,
    ringkasan_hasil TEXT NULL,
    status ENUM('BELUM_DINILAI','SEDANG_DINILAI','SELESAI','DIKUNCI') NOT NULL DEFAULT 'BELUM_DINILAI',
    unit_scope_id BIGINT UNSIGNED GENERATED ALWAYS AS (COALESCE(unit_id, 0)) STORED,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_evaluasi_unit (evaluasi_id, unit_scope_id),
    INDEX idx_evaluasi_unit_unit (unit_id),
    INDEX idx_evaluasi_unit_status (evaluasi_id, status),
    INDEX idx_evaluasi_unit_predikat (predikat_id),
    CONSTRAINT chk_evaluasi_unit_nilai CHECK (nilai_total IS NULL OR nilai_total >= 0),
    FOREIGN KEY (evaluasi_id) REFERENCES evaluasi_akip(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (unit_id) REFERENCES unit_organisasi(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (predikat_id) REFERENCES ref_predikat_sakip(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE evaluasi_lke_jawaban (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    evaluasi_unit_id BIGINT UNSIGNED NOT NULL,
    kriteria_id BIGINT UNSIGNED NOT NULL,
    nilai DECIMAL(6,2) NULL,
    jawaban_teks TEXT NULL,
    catatan TEXT NULL,
    dokumen_bukti_id BIGINT UNSIGNED NULL,
    penilai_user_id BIGINT UNSIGNED NULL,
    dinilai_at DATETIME NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_jawaban_kriteria (evaluasi_unit_id, kriteria_id),
    INDEX idx_jawaban_penilai (penilai_user_id, dinilai_at),
    INDEX idx_jawaban_bukti (dokumen_bukti_id),
    CONSTRAINT chk_evaluasi_lke_nilai CHECK (nilai IS NULL OR nilai >= 0),
    FOREIGN KEY (evaluasi_unit_id) REFERENCES evaluasi_unit(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (kriteria_id) REFERENCES lke_kriteria(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (dokumen_bukti_id) REFERENCES dokumen_bukti(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (penilai_user_id) REFERENCES app_user(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE evaluasi_temuan (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    evaluasi_unit_id BIGINT UNSIGNED NOT NULL,
    komponen_id BIGINT UNSIGNED NULL,
    kriteria_id BIGINT UNSIGNED NULL,
    jenis_temuan ENUM('KELEMAHAN','KEKUATAN','RISIKO','KETIDAKSESUAIAN','PELUANG_PERBAIKAN') NOT NULL,
    uraian TEXT NOT NULL,
    sebab TEXT NULL,
    akibat TEXT NULL,
    tingkat_risiko ENUM('RENDAH','SEDANG','TINGGI','KRITIS') NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_temuan_unit_risiko (evaluasi_unit_id, tingkat_risiko),
    INDEX idx_temuan_komponen (komponen_id),
    INDEX idx_temuan_kriteria (kriteria_id),
    FOREIGN KEY (evaluasi_unit_id) REFERENCES evaluasi_unit(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (komponen_id) REFERENCES lke_komponen(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (kriteria_id) REFERENCES lke_kriteria(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE evaluasi_rekomendasi (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    temuan_id BIGINT UNSIGNED NOT NULL,
    rekomendasi TEXT NOT NULL,
    prioritas ENUM('RENDAH','SEDANG','TINGGI') NOT NULL DEFAULT 'SEDANG',
    batas_waktu DATE NULL,
    unit_penanggung_jawab_id BIGINT UNSIGNED NULL,
    status ENUM('BARU','DITINDAKLANJUTI','SELESAI','TIDAK_DAPAT_DITINDAKLANJUTI') NOT NULL DEFAULT 'BARU',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_rekomendasi_status_deadline (status, batas_waktu),
    INDEX idx_rekomendasi_unit_status (unit_penanggung_jawab_id, status),
    FOREIGN KEY (temuan_id) REFERENCES evaluasi_temuan(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (unit_penanggung_jawab_id) REFERENCES unit_organisasi(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE evaluasi_tindak_lanjut (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    rekomendasi_id BIGINT UNSIGNED NOT NULL,
    uraian_tindak_lanjut TEXT NOT NULL,
    tanggal_tindak_lanjut DATE NOT NULL,
    progres_persen DECIMAL(6,2) NOT NULL DEFAULT 0,
    status ENUM('DRAFT','DIAJUKAN','VALID','DITOLAK','SELESAI') NOT NULL DEFAULT 'DRAFT',
    verifikator_user_id BIGINT UNSIGNED NULL,
    catatan_verifikasi TEXT NULL,
    verified_at DATETIME NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_tindak_lanjut_status_tanggal (status, tanggal_tindak_lanjut),
    INDEX idx_tindak_lanjut_verifikator (verifikator_user_id, verified_at),
    CONSTRAINT chk_tindak_lanjut_progres CHECK (progres_persen BETWEEN 0 AND 100),
    FOREIGN KEY (rekomendasi_id) REFERENCES evaluasi_rekomendasi(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (verifikator_user_id) REFERENCES app_user(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE evaluasi_tindak_lanjut_bukti (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    tindak_lanjut_id BIGINT UNSIGNED NOT NULL,
    dokumen_bukti_id BIGINT UNSIGNED NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_tindak_lanjut_bukti (tindak_lanjut_id, dokumen_bukti_id),
    FOREIGN KEY (tindak_lanjut_id) REFERENCES evaluasi_tindak_lanjut(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (dokumen_bukti_id) REFERENCES dokumen_bukti(id) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE workflow_instance (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    pemda_id BIGINT UNSIGNED NOT NULL,
    unit_id BIGINT UNSIGNED NULL,
    objek_tipe VARCHAR(80) NOT NULL,
    objek_id BIGINT UNSIGNED NOT NULL,
    nama_workflow VARCHAR(150) NOT NULL,
    status ENUM('DRAFT','PROSES','DISETUJUI','DITOLAK','REVISI','DIBATALKAN','SELESAI') NOT NULL DEFAULT 'DRAFT',
    created_by BIGINT UNSIGNED NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_workflow_objek (objek_tipe, objek_id),
    INDEX idx_workflow_scope_status (pemda_id, unit_id, status, created_at),
    INDEX idx_workflow_created_by (created_by, created_at),
    FOREIGN KEY (pemda_id) REFERENCES pemda(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (unit_id) REFERENCES unit_organisasi(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (created_by) REFERENCES app_user(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE workflow_step (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    workflow_id BIGINT UNSIGNED NOT NULL,
    urutan INT NOT NULL,
    nama_step VARCHAR(150) NOT NULL,
    role_id BIGINT UNSIGNED NULL,
    user_id BIGINT UNSIGNED NULL,
    status ENUM('MENUNGGU','DIPROSES','DISETUJUI','DITOLAK','DILEWATI') NOT NULL DEFAULT 'MENUNGGU',
    acted_at DATETIME NULL,
    catatan TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_workflow_step_urutan (workflow_id, urutan),
    INDEX idx_workflow_step_user_status (user_id, status),
    INDEX idx_workflow_step_role_status (role_id, status),
    FOREIGN KEY (workflow_id) REFERENCES workflow_instance(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES app_role(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES app_user(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE workflow_log (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    workflow_id BIGINT UNSIGNED NOT NULL,
    step_id BIGINT UNSIGNED NULL,
    user_id BIGINT UNSIGNED NULL,
    aksi VARCHAR(100) NOT NULL,
    catatan TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_workflow_log_time (workflow_id, created_at),
    INDEX idx_workflow_log_user_time (user_id, created_at),
    FOREIGN KEY (workflow_id) REFERENCES workflow_instance(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (step_id) REFERENCES workflow_step(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES app_user(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ai_review_job (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    pemda_id BIGINT UNSIGNED NOT NULL,
    unit_id BIGINT UNSIGNED NULL,
    objek_tipe VARCHAR(80) NOT NULL,
    objek_id BIGINT UNSIGNED NOT NULL,
    jenis_review ENUM('KUALITAS_INDIKATOR','CASCADING','LKJIP','LKE','RENSTRA','RENJA','PK','CAPAIAN','LAINNYA') NOT NULL,
    prompt_ringkas TEXT NULL,
    status ENUM('ANTRI','PROSES','SELESAI','GAGAL') NOT NULL DEFAULT 'ANTRI',
    requested_by BIGINT UNSIGNED NULL,
    requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at DATETIME NULL,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ai_review_objek (objek_tipe, objek_id),
    INDEX idx_ai_review_scope (pemda_id, unit_id, jenis_review, status),
    INDEX idx_ai_review_status_time (status, requested_at),
    FOREIGN KEY (pemda_id) REFERENCES pemda(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (unit_id) REFERENCES unit_organisasi(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (requested_by) REFERENCES app_user(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ai_review_result (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    job_id BIGINT UNSIGNED NOT NULL,
    skor DECIMAL(6,2) NULL,
    ringkasan TEXT NULL,
    masalah TEXT NULL,
    rekomendasi TEXT NULL,
    json_result JSON NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_ai_review_result_job (job_id),
    FOREIGN KEY (job_id) REFERENCES ai_review_job(id) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE audit_log (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NULL,
    pemda_id BIGINT UNSIGNED NULL,
    unit_id BIGINT UNSIGNED NULL,
    aksi VARCHAR(100) NOT NULL,
    tabel VARCHAR(100) NULL,
    record_id BIGINT UNSIGNED NULL,
    before_json JSON NULL,
    after_json JSON NULL,
    ip_address VARCHAR(80) NULL,
    user_agent TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_objek (tabel, record_id),
    INDEX idx_audit_user_time (user_id, created_at),
    INDEX idx_audit_scope_time (pemda_id, unit_id, created_at),
    INDEX idx_audit_aksi_time (aksi, created_at),
    FOREIGN KEY (user_id) REFERENCES app_user(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (pemda_id) REFERENCES pemda(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (unit_id) REFERENCES unit_organisasi(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
