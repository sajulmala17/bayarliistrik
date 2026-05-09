# ⚡ Aplikasi Pembayaran Listrik Pascabayar

Aplikasi web pengelolaan tagihan listrik berbasis **Flask + MariaDB**, tampil via browser.

---

## 📁 Struktur Folder

```
listrik_app/
├── app.py                  ← Backend Flask (API)
├── requirements.txt        ← Dependensi Python
├── JALANKAN.bat            ← Klik 2x untuk jalankan (Windows)
├── static/
│   └── index.html          ← Frontend (dark dashboard)
└── database/
    └── db_listrik.sql      ← Semua SQL (DDL + DML + View + SP + Func + Trigger)
```

---

## 🚀 Cara Menjalankan

### Langkah 1 — Siapkan Database

1. Buka **XAMPP** → klik **Start** pada MySQL/MariaDB
2. Buka **phpMyAdmin** → `http://localhost/phpmyadmin`
3. Pilih database **`db_listrik`** (sudah ada)
4. Klik tab **SQL** → paste isi file `database/db_listrik.sql` → klik **Go**

> ✅ Semua tabel, data awal, view, stored procedure, function, dan trigger akan dibuat otomatis.

### Langkah 2 — Install Dependensi Python

Buka Command Prompt di folder `listrik_app/`, jalankan:

```cmd
pip install flask flask-cors mysql-connector-python
```

### Langkah 3 — Jalankan Aplikasi

Klik 2x file **`JALANKAN.bat`** — atau via CMD:

```cmd
python app.py
```

Buka browser: **http://localhost:5000**

---

## 🔑 Akun Demo

| Role       | Username    | Password       |
|------------|-------------|----------------|
| Superadmin | superadmin  | admin123       |
| Admin      | admin01     | admin123       |
| Kasir      | kasir01     | kasir123       |
| Pelanggan  | plg001      | pelanggan123   |

---

## 🗄️ Objek Database yang Dibuat

### DDL — Tabel
| Tabel         | Keterangan |
|---------------|------------|
| `level`       | Role admin (superadmin, admin, kasir) |
| `user`        | Akun admin sistem |
| `tarif`       | Golongan tarif listrik per daya |
| `pelanggan`   | Data pelanggan PLN |
| `penggunaan`  | Catatan meter bulanan |
| `tagihan`     | Tagihan listrik (auto via trigger) |
| `pembayaran`  | Transaksi pembayaran |
| `log_aktivitas` | Audit trail aktivitas |

### DML — Data Awal
- `level`: 3 role (superadmin, admin, kasir)
- `user`: 4 akun admin
- `tarif`: 7 golongan daya (450W–6600W) — **dengan COMMIT**
- `pelanggan`: 10 pelanggan sample
- `penggunaan`: 15 data meter awal

### View
- **`v_info_penggunaan`** — Menampilkan info lengkap penggunaan listrik (JOIN pelanggan + tarif + tagihan)

### Stored Procedure
- **`sp_pelanggan_900watt()`** — Menampilkan semua pelanggan dengan daya 900 watt

### Function
- **`fn_total_penggunaan_perbulan(id_pelanggan, bulan, tahun)`** — Menghitung total kWh per bulan

### Trigger
- **`trg_after_insert_penggunaan`** — Otomatis membuat tagihan setelah INSERT data penggunaan
  - Hitung jumlah meter (kWh)
  - Hitung biaya pemakaian × tarif
  - Hitung PPJ 3%
  - Set jatuh tempo 20 hari ke depan

### Transaksi
- **COMMIT** setelah INSERT data tarif
- **ROLLBACK** demo hapus pelanggan (data tetap aman)

---

## ⚙️ Fitur Aplikasi

### Dashboard
- Statistik: total pelanggan, tagihan belum bayar, lunas, pendapatan bulan ini
- Grafik batang pendapatan 6 bulan terakhir
- Tabel tagihan terbaru

### Manajemen Pelanggan
- CRUD data pelanggan
- Pencarian by nama / nomor KWH

### Catat Meter
- Input data meter bulanan
- **Tagihan otomatis dibuat via TRIGGER**

### Tagihan
- Filter by status (belum bayar / sudah bayar)
- Proses pembayaran langsung dari tabel

### Pembayaran
- Riwayat semua transaksi
- Support tunai, transfer, QRIS

### Pelanggan 900W
- Menjalankan **Stored Procedure** `sp_pelanggan_900watt()`

### Kelola User Admin
- Tambah user admin/kasir

### Login Pelanggan
- Portal mandiri untuk cek tagihan & riwayat bayar

---

## 🛠️ Troubleshooting

**`mysql.connector.errors.DatabaseError: 2003 Can't connect`**
→ Pastikan MariaDB XAMPP sudah berjalan (klik START di XAMPP Control Panel)

**`ModuleNotFoundError: No module named 'flask'`**
→ Jalankan: `pip install flask flask-cors mysql-connector-python`

**Tabel sudah ada / error duplikat**
→ SQL menggunakan `IF NOT EXISTS` dan `CREATE OR REPLACE` sehingga aman dijalankan ulang

**Password MariaDB bukan kosong**
→ Edit `DB_CONFIG` di `app.py` baris ~20, ubah `'password': ''` menjadi password Anda
