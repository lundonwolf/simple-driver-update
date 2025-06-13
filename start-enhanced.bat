@echo off
title Windows Driver Updater - Enhanced v1.0.3
echo.
echo =====================================
echo Windows Driver Updater - Enhanced
echo =====================================
echo.
echo Starting the enhanced driver updater...
echo Please wait while the application loads...
echo.

REM Check if we're running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [INFO] Running with administrator privileges ✓
) else (
    echo [WARNING] Not running as administrator!
    echo [WARNING] Some features may not work properly.
    echo [WARNING] Please run this batch file as administrator.
    echo.
    pause
)

echo.
echo [INFO] Launching DriverUpdaterEnhanced.exe...
echo.

REM Try to run the enhanced executable
if exist "dist\DriverUpdaterEnhanced.exe" (
    cd dist
    DriverUpdaterEnhanced.exe
) else if exist "DriverUpdaterEnhanced.exe" (
    DriverUpdaterEnhanced.exe
) else if exist "main.py" (
    echo [INFO] Executable not found, running from source...
    python main.py
) else (
    echo [ERROR] Could not find the driver updater executable or source files!
    echo [ERROR] Please ensure you have the complete application files.
    echo.
    pause
    exit /b 1
)

echo.
echo [INFO] Driver updater closed.
echo.
pause
