-- ============================================================
-- APLIKASI PEMBAYARAN LISTRIK PASCABAYAR
-- Database: db_listrik | Engine: MariaDB (XAMPP)
-- ============================================================

USE db_listrik;

-- ============================================================
-- DDL: CREATE TABLES
-- ============================================================

-- Tabel level (role pengguna admin)
CREATE TABLE IF NOT EXISTS level (
    id_level    INT PRIMARY KEY AUTO_INCREMENT,
    nama_level  VARCHAR(50) NOT NULL,
    deskripsi   VARCHAR(100)
) ENGINE=InnoDB;

-- Tabel user (admin sistem)
CREATE TABLE IF NOT EXISTS user (
    id_user     INT PRIMARY KEY AUTO_INCREMENT,
    username    VARCHAR(50) NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,  -- disimpan sebagai hash SHA2
    nama_admin  VARCHAR(100) NOT NULL,
    id_level    INT NOT NULL,
    email       VARCHAR(100),
    hp          VARCHAR(20),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_level) REFERENCES level(id_level)
) ENGINE=InnoDB;

-- Tabel tarif listrik
CREATE TABLE IF NOT EXISTS tarif (
    id_tarif    INT PRIMARY KEY AUTO_INCREMENT,
    daya        INT NOT NULL,           -- dalam watt, misal: 450, 900, 1300, 2200
    tarifperkwh DECIMAL(10,2) NOT NULL, -- rupiah per kWh
    nama_golongan VARCHAR(50),
    keterangan  VARCHAR(200)
) ENGINE=InnoDB;

-- Tabel pelanggan
CREATE TABLE IF NOT EXISTS pelanggan (
    id_pelanggan    INT PRIMARY KEY AUTO_INCREMENT,
    username        VARCHAR(50) NOT NULL UNIQUE,
    password        VARCHAR(255) NOT NULL,
    nomor_kwh       VARCHAR(20) NOT NULL UNIQUE,
    nama_pelanggan  VARCHAR(100) NOT NULL,
    alamat          TEXT,
    id_tarif        INT NOT NULL,
    no_hp           VARCHAR(20),
    email           VARCHAR(100),
    status_aktif    TINYINT(1) DEFAULT 1,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_tarif) REFERENCES tarif(id_tarif)
) ENGINE=InnoDB;

-- Tabel penggunaan listrik (meter reading)
CREATE TABLE IF NOT EXISTS penggunaan (
    id_penggunaan   INT PRIMARY KEY AUTO_INCREMENT,
    id_pelanggan    INT NOT NULL,
    bulan           INT NOT NULL CHECK (bulan BETWEEN 1 AND 12),
    tahun           INT NOT NULL,
    meter_awal      DECIMAL(10,2) NOT NULL DEFAULT 0,
    meter_ahir      DECIMAL(10,2) NOT NULL DEFAULT 0,
    tanggal_catat   DATE,
    petugas         VARCHAR(100),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_pelanggan) REFERENCES pelanggan(id_pelanggan),
    UNIQUE KEY uk_penggunaan (id_pelanggan, bulan, tahun)
) ENGINE=InnoDB;

-- Tabel tagihan (dibuat otomatis via TRIGGER)
CREATE TABLE IF NOT EXISTS tagihan (
    id_tagihan      INT PRIMARY KEY AUTO_INCREMENT,
    id_penggunaan   INT NOT NULL,
    id_pelanggan    INT NOT NULL,
    bulan           INT NOT NULL,
    tahun           INT NOT NULL,
    jumlah_meter    DECIMAL(10,2) NOT NULL DEFAULT 0,
    biaya_pemakaian DECIMAL(15,2) DEFAULT 0,
    biaya_beban     DECIMAL(15,2) DEFAULT 0,
    ppj             DECIMAL(15,2) DEFAULT 0,    -- Pajak Penerangan Jalan 3%
    total_tagihan   DECIMAL(15,2) DEFAULT 0,
    status          ENUM('belum_bayar','sudah_bayar','cicilan') DEFAULT 'belum_bayar',
    tanggal_tagihan DATE,
    jatuh_tempo     DATE,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_penggunaan) REFERENCES penggunaan(id_penggunaan),
    FOREIGN KEY (id_pelanggan) REFERENCES pelanggan(id_pelanggan)
) ENGINE=InnoDB;

-- Tabel pembayaran
CREATE TABLE IF NOT EXISTS pembayaran (
    id_pembayaran       INT PRIMARY KEY AUTO_INCREMENT,
    id_tagihan          INT NOT NULL,
    id_pelanggan        INT NOT NULL,
    tanggal_pembayaran  DATE NOT NULL,
    bulan_bayar         INT NOT NULL,
    tahun_bayar         INT NOT NULL,
    biaya_admin         DECIMAL(10,2) DEFAULT 2500,
    total_bayar         DECIMAL(15,2) NOT NULL,
    id_user             INT NOT NULL,           -- kasir/admin yang memproses
    metode_bayar        ENUM('tunai','transfer','qris') DEFAULT 'tunai',
    no_referensi        VARCHAR(50),            -- nomor referensi transaksi
    keterangan          TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_tagihan) REFERENCES tagihan(id_tagihan),
    FOREIGN KEY (id_pelanggan) REFERENCES pelanggan(id_pelanggan),
    FOREIGN KEY (id_user) REFERENCES user(id_user)
) ENGINE=InnoDB;

-- Tabel log aktivitas (tambahan untuk audit trail)
CREATE TABLE IF NOT EXISTS log_aktivitas (
    id_log      INT PRIMARY KEY AUTO_INCREMENT,
    id_user     INT,
    aksi        VARCHAR(100),
    tabel_terkait VARCHAR(50),
    id_record   INT,
    keterangan  TEXT,
    ip_address  VARCHAR(45),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- DML: INSERT DATA AWAL
-- ============================================================

-- INSERT Tabel level
INSERT INTO level (nama_level, deskripsi) VALUES
('superadmin', 'Akses penuh seluruh sistem'),
('admin',       'Akses kelola data pelanggan dan tagihan'),
('kasir',       'Akses input pembayaran saja');

-- INSERT Tabel user (password = SHA2('password123', 256))
INSERT INTO user (username, password, nama_admin, id_level, email, hp) VALUES
('superadmin', SHA2('admin123', 256),   'Super Administrator', 1, 'super@pln.co.id',  '08111000001'),
('admin01',    SHA2('admin123', 256),   'Budi Santoso',        2, 'budi@pln.co.id',   '08111000002'),
('kasir01',    SHA2('kasir123', 256),   'Siti Rahayu',         3, 'siti@pln.co.id',   '08111000003'),
('kasir02',    SHA2('kasir123', 256),   'Ahmad Fauzi',         3, 'ahmad@pln.co.id',  '08111000004');

-- INSERT Tabel tarif (dengan COMMIT sesuai ketentuan)
START TRANSACTION;
INSERT INTO tarif (daya, tarifperkwh, nama_golongan, keterangan) VALUES
(450,  415.00,  'R-1/TR 450 VA',   'Rumah tangga sangat kecil'),
(900,  605.00,  'R-1/TR 900 VA',   'Rumah tangga kecil'),
(1300, 1352.00, 'R-1/TR 1300 VA',  'Rumah tangga menengah'),
(2200, 1352.00, 'R-1/TR 2200 VA',  'Rumah tangga menengah atas'),
(3500, 1444.70, 'R-2/TR 3500 VA',  'Rumah tangga besar'),
(5500, 1444.70, 'R-3/TR 5500 VA',  'Rumah tangga sangat besar'),
(6600, 1444.70, 'B-2/TR 6600 VA',  'Bisnis menengah');
COMMIT;

-- INSERT Tabel pelanggan
INSERT INTO pelanggan (username, password, nomor_kwh, nama_pelanggan, alamat, id_tarif, no_hp, email) VALUES
('plg001', SHA2('pelanggan123', 256), '5210001001', 'Andi Wijaya',       'Jl. Merdeka No.1, Jakarta Selatan',   2, '08122000001', 'andi@email.com'),
('plg002', SHA2('pelanggan123', 256), '5210001002', 'Budi Kurniawan',    'Jl. Sudirman No.25, Jakarta Pusat',   2, '08122000002', 'budi@email.com'),
('plg003', SHA2('pelanggan123', 256), '5210001003', 'Citra Dewi',        'Jl. Gatot Subroto No.7, Jakarta',     3, '08122000003', 'citra@email.com'),
('plg004', SHA2('pelanggan123', 256), '5210001004', 'Doni Saputra',      'Jl. HR Rasuna Said, Jakarta Selatan', 1, '08122000004', 'doni@email.com'),
('plg005', SHA2('pelanggan123', 256), '5210001005', 'Eka Fitriani',      'Jl. Thamrin No.15, Jakarta Pusat',    4, '08122000005', 'eka@email.com'),
('plg006', SHA2('pelanggan123', 256), '5210001006', 'Fajar Nugroho',     'Jl. Kebon Sirih No.33, Jakarta',      2, '08122000006', 'fajar@email.com'),
('plg007', SHA2('pelanggan123', 256), '5210001007', 'Gita Permatasari',  'Jl. Casablanca No.88, Jakarta',       3, '08122000007', 'gita@email.com'),
('plg008', SHA2('pelanggan123', 256), '5210001008', 'Hendra Gunawan',    'Jl. MT Haryono No.12, Jakarta',       2, '08122000008', 'hendra@email.com'),
('plg009', SHA2('pelanggan123', 256), '5210001009', 'Indah Kusuma',      'Jl. Pancoran No.5, Jakarta Selatan',  1, '08122000009', 'indah@email.com'),
('plg010', SHA2('pelanggan123', 256), '5210001010', 'Joko Widodo',       'Jl. Semanggi No.9, Jakarta Pusat',    5, '08122000010', 'joko@email.com');

-- INSERT Tabel penggunaan (data 3 bulan terakhir)
INSERT INTO penggunaan (id_pelanggan, bulan, tahun, meter_awal, meter_ahir, tanggal_catat, petugas) VALUES
(1, 2, 2026, 1200.00, 1345.00, '2026-02-28', 'Petugas A'),
(2, 2, 2026,  850.00,  978.00, '2026-02-28', 'Petugas A'),
(3, 2, 2026, 2100.00, 2267.00, '2026-02-28', 'Petugas B'),
(4, 2, 2026,  430.00,  498.00, '2026-02-28', 'Petugas B'),
(5, 2, 2026, 3300.00, 3521.00, '2026-02-28', 'Petugas A'),
(1, 3, 2026, 1345.00, 1489.00, '2026-03-31', 'Petugas A'),
(2, 3, 2026,  978.00, 1102.00, '2026-03-31', 'Petugas A'),
(3, 3, 2026, 2267.00, 2445.00, '2026-03-31', 'Petugas B'),
(4, 3, 2026,  498.00,  571.00, '2026-03-31', 'Petugas B'),
(5, 3, 2026, 3521.00, 3788.00, '2026-03-31', 'Petugas A'),
(6, 3, 2026,  500.00,  632.00, '2026-03-31', 'Petugas C'),
(7, 3, 2026,  700.00,  856.00, '2026-03-31', 'Petugas C'),
(8, 3, 2026,  320.00,  445.00, '2026-03-31', 'Petugas C'),
(9, 3, 2026,  200.00,  289.00, '2026-03-31', 'Petugas C'),
(10, 3, 2026, 5000.00, 5234.00,'2026-03-31', 'Petugas C');

-- ============================================================
-- VIEW: Informasi Penggunaan Listrik
-- ============================================================
CREATE OR REPLACE VIEW v_info_penggunaan AS
SELECT
    pg.id_penggunaan,
    pl.nomor_kwh,
    pl.nama_pelanggan,
    pl.alamat,
    t.daya,
    t.nama_golongan,
    t.tarifperkwh,
    pg.bulan,
    pg.tahun,
    CONCAT(
        CASE pg.bulan
            WHEN 1  THEN 'Januari'   WHEN 2  THEN 'Februari' WHEN 3  THEN 'Maret'
            WHEN 4  THEN 'April'     WHEN 5  THEN 'Mei'      WHEN 6  THEN 'Juni'
            WHEN 7  THEN 'Juli'      WHEN 8  THEN 'Agustus'  WHEN 9  THEN 'September'
            WHEN 10 THEN 'Oktober'   WHEN 11 THEN 'November' WHEN 12 THEN 'Desember'
        END, ' ', pg.tahun
    ) AS periode,
    pg.meter_awal,
    pg.meter_ahir,
    (pg.meter_ahir - pg.meter_awal) AS jumlah_kwh,
    ((pg.meter_ahir - pg.meter_awal) * t.tarifperkwh) AS biaya_pemakaian,
    ((pg.meter_ahir - pg.meter_awal) * t.tarifperkwh * 0.03) AS ppj,
    ((pg.meter_ahir - pg.meter_awal) * t.tarifperkwh * 1.03) AS estimasi_tagihan,
    pg.tanggal_catat,
    pg.petugas,
    IFNULL(tg.status, 'belum_dihitung') AS status_tagihan
FROM penggunaan pg
JOIN pelanggan pl ON pg.id_pelanggan = pl.id_pelanggan
JOIN tarif t ON pl.id_tarif = t.id_tarif
LEFT JOIN tagihan tg ON pg.id_penggunaan = tg.id_penggunaan
ORDER BY pg.tahun DESC, pg.bulan DESC, pl.nama_pelanggan ASC;

-- ============================================================
-- STORED PROCEDURE: Pelanggan dengan daya 900 watt
-- ============================================================
DELIMITER //

CREATE PROCEDURE IF NOT EXISTS sp_pelanggan_900watt()
BEGIN
    SELECT
        pl.id_pelanggan,
        pl.nomor_kwh,
        pl.nama_pelanggan,
        pl.alamat,
        pl.no_hp,
        pl.email,
        t.daya,
        t.nama_golongan,
        t.tarifperkwh,
        pl.status_aktif,
        pl.created_at
    FROM pelanggan pl
    JOIN tarif t ON pl.id_tarif = t.id_tarif
    WHERE t.daya = 900
      AND pl.status_aktif = 1
    ORDER BY pl.nama_pelanggan ASC;
END //

-- ============================================================
-- FUNCTION: Hitung total penggunaan listrik per bulan (kWh)
-- ============================================================

CREATE FUNCTION IF NOT EXISTS fn_total_penggunaan_perbulan(
    p_id_pelanggan INT,
    p_bulan INT,
    p_tahun INT
)
RETURNS DECIMAL(10,2)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE total_kwh DECIMAL(10,2) DEFAULT 0;

    SELECT COALESCE(SUM(meter_ahir - meter_awal), 0)
    INTO total_kwh
    FROM penggunaan
    WHERE id_pelanggan = p_id_pelanggan
      AND bulan = p_bulan
      AND tahun = p_tahun;

    RETURN total_kwh;
END //

-- ============================================================
-- TRIGGER: Auto-insert tagihan setelah insert penggunaan
-- ============================================================

CREATE TRIGGER IF NOT EXISTS trg_after_insert_penggunaan
AFTER INSERT ON penggunaan
FOR EACH ROW
BEGIN
    DECLARE v_tarifperkwh   DECIMAL(10,2);
    DECLARE v_id_tarif      INT;
    DECLARE v_jumlah_meter  DECIMAL(10,2);
    DECLARE v_biaya_pemakaian DECIMAL(15,2);
    DECLARE v_biaya_beban   DECIMAL(15,2);
    DECLARE v_ppj           DECIMAL(15,2);
    DECLARE v_total         DECIMAL(15,2);
    DECLARE v_tgl_tagihan   DATE;
    DECLARE v_jatuh_tempo   DATE;

    -- Ambil tarif pelanggan
    SELECT pl.id_tarif, t.tarifperkwh
    INTO v_id_tarif, v_tarifperkwh
    FROM pelanggan pl
    JOIN tarif t ON pl.id_tarif = t.id_tarif
    WHERE pl.id_pelanggan = NEW.id_pelanggan;

    -- Hitung komponen tagihan
    SET v_jumlah_meter   = NEW.meter_ahir - NEW.meter_awal;
    SET v_biaya_pemakaian = v_jumlah_meter * v_tarifperkwh;
    SET v_biaya_beban    = 0; -- bisa disesuaikan per golongan
    SET v_ppj            = v_biaya_pemakaian * 0.03;  -- PPJ 3%
    SET v_total          = v_biaya_pemakaian + v_biaya_beban + v_ppj;
    SET v_tgl_tagihan    = CURDATE();
    SET v_jatuh_tempo    = DATE_ADD(CURDATE(), INTERVAL 20 DAY); -- jatuh tempo 20 hari

    -- Insert ke tabel tagihan
    INSERT INTO tagihan (
        id_penggunaan, id_pelanggan, bulan, tahun,
        jumlah_meter, biaya_pemakaian, biaya_beban, ppj, total_tagihan,
        status, tanggal_tagihan, jatuh_tempo
    ) VALUES (
        NEW.id_penggunaan, NEW.id_pelanggan, NEW.bulan, NEW.tahun,
        v_jumlah_meter, v_biaya_pemakaian, v_biaya_beban, v_ppj, v_total,
        'belum_bayar', v_tgl_tagihan, v_jatuh_tempo
    );
END //

DELIMITER ;

-- ============================================================
-- DEMO ROLLBACK: Hapus 1 pelanggan lalu rollback
-- ============================================================
START TRANSACTION;
DELETE FROM pelanggan WHERE id_pelanggan = 10;
-- Cek dulu...
SELECT COUNT(*) AS sisa_pelanggan FROM pelanggan;
ROLLBACK;  -- Batalkan penghapusan
-- Data kembali seperti semula
SELECT COUNT(*) AS sisa_pelanggan_setelah_rollback FROM pelanggan;

-- ============================================================
-- Konfirmasi semua objek berhasil dibuat
-- ============================================================
SHOW TABLES;
SELECT 'Database db_listrik berhasil dikonfigurasi!' AS status;
