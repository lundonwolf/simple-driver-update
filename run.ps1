# Windows Driver Updater PowerShell Launcher with Auto-Admin
# Run with: powershell -ExecutionPolicy Bypass -File run.ps1

param(
    [switch]$InstallDependencies,
    [switch]$Verbose,
    [switch]$SkipAdminCheck
)

$ErrorActionPreference = "Stop"

Write-Host "Windows Driver Updater" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan
Write-Host ""

# Check PowerShell version
if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Host "ERROR: PowerShell 5.0 or later is required." -ForegroundColor Red
    Write-Host "Please update PowerShell or use the batch file instead." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

# Auto-request admin privileges if not already running as admin
if (-not $isAdmin -and -not $SkipAdminCheck) {
    Write-Host "Administrator privileges required for driver operations." -ForegroundColor Yellow
    Write-Host "Requesting administrator privileges..." -ForegroundColor Yellow
    
    try {
        # Build arguments to pass to elevated process
        $arguments = "-ExecutionPolicy Bypass -File `"$($MyInvocation.MyCommand.Path)`""
        if ($InstallDependencies) { $arguments += " -InstallDependencies" }
        if ($Verbose) { $arguments += " -Verbose" }
        $arguments += " -SkipAdminCheck"  # Prevent infinite loop
        
        Start-Process powershell -ArgumentList $arguments -Verb RunAs -Wait
        exit 0
    } catch {
        Write-Host "ERROR: Failed to request administrator privileges." -ForegroundColor Red
        Write-Host "Please right-click and 'Run as Administrator' manually." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

if ($isAdmin) {
    Write-Host "Running with administrator privileges." -ForegroundColor Green
} else {
    Write-Host "WARNING: Not running as administrator." -ForegroundColor Yellow
    Write-Host "Some features may not work properly." -ForegroundColor Yellow
}
Write-Host ""

# Change to script directory
Set-Location $PSScriptRoot

# Check Python installation
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Python 3.8 or later from https://python.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install dependencies if requested or missing
if ($InstallDependencies -or -not (Test-Path "requirements_installed.flag")) {
    Write-Host "Installing/updating dependencies..." -ForegroundColor Yellow
    
    try {
        python -m pip install --upgrade pip
        python -m pip install -r requirements.txt
        
        # Create flag file to indicate dependencies are installed
        New-Item -Path "requirements_installed.flag" -ItemType File -Force | Out-Null
        Write-Host "Dependencies installed successfully." -ForegroundColor Green
    } catch {
        Write-Host "ERROR: Failed to install dependencies." -ForegroundColor Red
        Write-Host "Please run manually: python -m pip install -r requirements.txt" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "Checking dependencies..." -ForegroundColor Yellow
    
    # Quick check if main modules are available
    $checkScript = @"
try:
    import tkinter, requests, psutil, wmi, win32api
    print("Dependencies OK")
except ImportError as e:
    print(f"Missing dependency: {e}")
    exit(1)
"@
    
    $result = python -c $checkScript 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Missing dependencies detected. Installing..." -ForegroundColor Yellow
        python -m pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERROR: Failed to install dependencies." -ForegroundColor Red
            Read-Host "Press Enter to exit"
            exit 1
        }
    } else {
        Write-Host "Dependencies OK" -ForegroundColor Green
    }
}

# Start the application
Write-Host ""
Write-Host "Starting Driver Updater..." -ForegroundColor Green
Write-Host ""

try {
    if ($Verbose) {
        python main.py --verbose
    } else {
        python main.py
    }
} catch {
    Write-Host ""
    Write-Host "Application encountered an error." -ForegroundColor Red
    Write-Host "Error details: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Application exited with error code: $LASTEXITCODE" -ForegroundColor Red
    Read-Host "Press Enter to continue"
}
