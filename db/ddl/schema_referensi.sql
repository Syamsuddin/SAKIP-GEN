-- Skema REFERENSI (asumsi) untuk SAKIP-Gen Fase 1.
-- SESUAIKAN dengan skema aplikasi SAKIP Anda yang sebenarnya: jalankan
-- SHOW CREATE TABLE pada tabel asli, lalu samakan nama tabel/kolom di db/queries.py.

CREATE TABLE opd (
  id   INT PRIMARY KEY,
  kode VARCHAR(20),
  nama VARCHAR(150)
);

CREATE TABLE sasaran_strategis (
  id     INT PRIMARY KEY,
  opd_id INT,
  tahun  SMALLINT,
  kode   VARCHAR(20),
  uraian VARCHAR(255)
);

CREATE TABLE indikator (
  id         INT PRIMARY KEY,
  sasaran_id INT,
  kode       VARCHAR(30),
  uraian     VARCHAR(255),
  satuan     VARCHAR(40),
  tipologi   VARCHAR(20)   -- input | proses | output | outcome | impact
);

CREATE TABLE capaian_kinerja (
  id           INT PRIMARY KEY,
  indikator_id INT,
  opd_id       INT,
  tahun        SMALLINT,
  target       DECIMAL(15,2),
  realisasi    DECIMAL(15,2)
);

-- Flag pelaporan & evaluasi internal (boleh berasal dari modul lain/manual).
CREATE TABLE pelaporan_meta (
  opd_id                INT,
  tahun                 SMALLINT,
  ada_lkjip             TINYINT,
  ada_analisis_capaian  TINYINT,
  ada_analisis_efisiensi TINYINT,
  ada_evaluasi_internal TINYINT,
  ada_tindak_lanjut     TINYINT
);

-- User read-only khusus SAKIP-Gen (hanya boleh membaca):
-- CREATE USER 'sakip_ro'@'127.0.0.1' IDENTIFIED BY '...';
-- GRANT SELECT ON sakip.* TO 'sakip_ro'@'127.0.0.1';
-- FLUSH PRIVILEGES;
