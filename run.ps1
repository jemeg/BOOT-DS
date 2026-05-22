Write-Host "================================" -ForegroundColor Cyan
Write-Host "   بوت وزارة الصحة - التشغيل   " -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $scriptPath

if (-not (Test-Path -LiteralPath "node_modules")) {
    Write-Host "📦 جاري تثبيت المكتبات..." -ForegroundColor Yellow
    npm install
    if (-not $?) {
        Write-Host "❌ فشل التثبيت" -ForegroundColor Red
        Read-Host "اضغط Enter للخروج"
        exit 1
    }
}

if (-not (Test-Path -LiteralPath ".env")) {
    Write-Host "⚠️  لم يتم العثور على ملف .env" -ForegroundColor Yellow
    Write-Host "   انسخ .env.example إلى .env وعدل الإعدادات" -ForegroundColor Yellow
}

Write-Host "🚀 تشغيل البوت..." -ForegroundColor Green
node server.js

if (-not $?) {
    Write-Host ""
    Write-Host "❌ حدث خطأ!" -ForegroundColor Red
    Read-Host "اضغط Enter للخروج"
}
