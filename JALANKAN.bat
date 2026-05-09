@echo off
title Aplikasi Listrik Pascabayar - Installer
color 0B
echo.
echo  ============================================
echo   APLIKASI LISTRIK PASCABAYAR
echo   Setup Otomatis - Windows 11
echo  ============================================
echo.

:: Pastikan Python tersedia
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python tidak ditemukan. Pastikan Python sudah terinstall.
    pause & exit /b 1
)

:: Install dependencies
echo [1/3] Menginstall dependensi Python...
pip install flask flask-cors mysql-connector-python --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Gagal install dependencies. Coba: pip install -r requirements.txt
    pause & exit /b 1
)
echo     OK - Flask, Flask-CORS, mysql-connector-python terinstall

echo.
echo [2/3] Pastikan XAMPP/MariaDB sudah berjalan...
echo     - Jalankan XAMPP dan klik START pada MySQL/MariaDB
echo     - Buka phpMyAdmin dan jalankan file: database/db_listrik.sql
echo.
pause

echo [3/3] Menjalankan aplikasi web...
echo.
echo  ============================================
echo   Buka browser: http://localhost:5000
echo.
echo   Login Admin   : superadmin / admin123
echo   Login Kasir   : kasir01 / kasir123
echo   Login Pelanggan: plg001 / pelanggan123
echo  ============================================
echo.

:: Buka browser otomatis setelah 2 detik
start "" /B timeout /t 2 >nul
start "" "http://localhost:5000"

:: Jalankan Flask
python app.py

pause
