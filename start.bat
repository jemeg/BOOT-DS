@echo off
title بوت وزارة الصحة
cd /d "%~dp0"
echo ================================
echo    بوت وزارة الصحة - التشغيل
echo ================================
echo.
node server.js
if %errorlevel% neq 0 (
    echo.
    echo ❌ حدث خطأ! تأكد من تثبيت المكتبات عبر: npm install
    pause
)
