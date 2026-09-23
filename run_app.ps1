# SmartVision startup script with workarounds for system clock issues
# This disables Cloudinary uploads and runs the app in resilient mode

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SmartVision - Starting with Workarounds" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check system clock status
Write-Host "[*] Checking system clock status..." -ForegroundColor Yellow
$clockStatus = w32tm /query /status
if ($clockStatus -match "not synchronized") {
    Write-Host "[!] WARNING: System clock is NOT synchronized!" -ForegroundColor Red
    Write-Host "    This will cause Cloudinary and Firebase authentication failures." -ForegroundColor Red
    Write-Host ""
    Write-Host "    TO FIX (requires Administrator):" -ForegroundColor Yellow
    Write-Host "    1. Open PowerShell as Administrator" -ForegroundColor Yellow
    Write-Host "    2. Run: w32tm /resync /force" -ForegroundColor Yellow
    Write-Host "    3. Restart this script" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "[✓] System clock is synchronized" -ForegroundColor Green
}

Write-Host ""
Write-Host "[*] Starting SmartVision app..." -ForegroundColor Cyan
Write-Host "    Cloudinary uploads: DISABLED" -ForegroundColor Yellow
Write-Host "    Firebase alerts: ENABLED (with retry logic)" -ForegroundColor Green
Write-Host ""

# Set environment variable to disable Cloudinary
$env:DISABLE_CLOUDINARY_UPLOAD = "1"

# Start the Flask app
python app.py
