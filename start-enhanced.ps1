# Windows Driver Updater - Enhanced v1.0.3
# PowerShell Launcher Script

$Host.UI.RawUI.WindowTitle = "Windows Driver Updater - Enhanced v1.0.3"

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Windows Driver Updater - Enhanced" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting the enhanced driver updater..." -ForegroundColor Yellow
Write-Host "Please wait while the application loads..." -ForegroundColor Yellow
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if ($isAdmin) {
    Write-Host "[INFO] Running with administrator privileges ✓" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Not running as administrator!" -ForegroundColor Red
    Write-Host "[WARNING] Some features may not work properly." -ForegroundColor Yellow
    Write-Host "[WARNING] Please run PowerShell as administrator and try again." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to continue anyway, or Ctrl+C to exit"
}

Write-Host ""
Write-Host "[INFO] Launching DriverUpdaterEnhanced.exe..." -ForegroundColor Green
Write-Host ""

# Try to run the enhanced executable
try {
    if (Test-Path "dist\DriverUpdaterEnhanced.exe") {
        Set-Location "dist"
        Start-Process ".\DriverUpdaterEnhanced.exe" -Wait
    } elseif (Test-Path "DriverUpdaterEnhanced.exe") {
        Start-Process ".\DriverUpdaterEnhanced.exe" -Wait
    } elseif (Test-Path "main.py") {
        Write-Host "[INFO] Executable not found, running from source..." -ForegroundColor Yellow
        python main.py
    } else {
        Write-Host "[ERROR] Could not find the driver updater executable or source files!" -ForegroundColor Red
        Write-Host "[ERROR] Please ensure you have the complete application files." -ForegroundColor Red
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
} catch {
    Write-Host "[ERROR] Failed to start the application: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[INFO] Driver updater closed." -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to exit"
