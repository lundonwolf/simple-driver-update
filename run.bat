@echo off
title Windows Driver Updater - Auto Admin
echo.
echo Windows Driver Updater
echo =====================
echo.

REM Check if already running as administrator
net session >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo Running with administrator privileges.
    goto :main
)

REM Not running as admin - request elevation
echo Administrator privileges required for driver operations.
echo Requesting administrator privileges...
echo.

REM Create a VBScript to request elevation
echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
echo UAC.ShellExecute "cmd.exe", "/c ""%~s0""", "", "runas", 1 >> "%temp%\getadmin.vbs"

REM Run the VBScript to elevate
"%temp%\getadmin.vbs"

REM Clean up
del "%temp%\getadmin.vbs"
exit /B

:main
REM Main program execution with admin privileges
echo Administrator privileges confirmed.
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.8 or later from https://python.org
    echo.
    pause
    exit /b 1
)

REM Check if requirements are installed
echo Checking dependencies...
python -c "import tkinter, requests, psutil, wmi, win32api" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Installing required packages...
    python -m pip install -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to install required packages.
        echo Please run: python -m pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
)

echo Starting Driver Updater...
echo.
python main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Driver Updater exited with error code %ERRORLEVEL%
    echo.
)

echo.
echo Driver Updater session completed.
pause
