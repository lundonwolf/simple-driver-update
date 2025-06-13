#!/usr/bin/env python3
"""
Build script for Windows Driver Updater
Creates a standalone executable using PyInstaller
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller

        return True
    except ImportError:
        return False


def install_pyinstaller():
    """Install PyInstaller"""
    try:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True
    except subprocess.CalledProcessError:
        return False


def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ["build", "dist"]

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name} directory...")
            shutil.rmtree(dir_name)


def create_spec_file():
    """Create PyInstaller spec file"""
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('README.md', '.'),
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'wmi',
        'win32api',
        'win32con',
        'requests',
        'psutil',
        'bs4',
        'packaging',
        'packaging.version',
        'packaging.specifiers',
        'packaging.requirements',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DriverUpdater',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DriverUpdater',
)
"""

    with open("DriverUpdater.spec", "w") as f:
        f.write(spec_content.strip())

    print("Created PyInstaller spec file")


def create_version_info():
    """Create version info file for executable"""
    version_info = """
# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Driver Updater Team'),
        StringStruct(u'FileDescription', u'Windows Driver Updater'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'DriverUpdater'),
        StringStruct(u'LegalCopyright', u'Copyright (C) 2024'),
        StringStruct(u'OriginalFilename', u'DriverUpdater.exe'),
        StringStruct(u'ProductName', u'Windows Driver Updater'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""

    with open("version_info.txt", "w") as f:
        f.write(version_info.strip())

    print("Created version info file")


def build_executable():
    """Build the executable using PyInstaller"""
    try:
        print("Building executable...")

        # Run PyInstaller
        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--clean", "DriverUpdater.spec"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("Executable built successfully!")
            return True
        else:
            print(f"Build failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"Error building executable: {e}")
        return False


def copy_additional_files():
    """Copy additional files to dist directory"""
    additional_files = [
        "README.md",
        "requirements.txt",
        "run.bat",
        "run.ps1",
    ]

    dist_dir = Path("dist/DriverUpdater")

    for file_name in additional_files:
        if os.path.exists(file_name):
            shutil.copy2(file_name, dist_dir / file_name)
            print(f"Copied {file_name}")


def create_installer():
    """Create NSIS installer script"""
    nsis_script = """
!define APP_NAME "Windows Driver Updater"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "Driver Updater Team"
!define APP_WEBSITE "https://github.com/your-repo/driver-updater"
!define APP_EXE "DriverUpdater.exe"

Name "${APP_NAME}"
OutFile "DriverUpdaterInstaller.exe"
InstallDir "$PROGRAMFILES\\${APP_NAME}"
InstallDirRegKey HKLM "Software\\${APP_NAME}" "InstallDir"
RequestExecutionLevel admin

Page directory
Page instfiles

Section "Install"
    SetOutPath "$INSTDIR"
    File /r "dist\\DriverUpdater\\*"
    
    WriteRegStr HKLM "Software\\${APP_NAME}" "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "UninstallString" "$INSTDIR\\uninstall.exe"
    
    CreateDirectory "$SMPROGRAMS\\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk" "$INSTDIR\\${APP_EXE}"
    CreateShortCut "$DESKTOP\\${APP_NAME}.lnk" "$INSTDIR\\${APP_EXE}"
    
    WriteUninstaller "$INSTDIR\\uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\\*.*"
    RMDir /r "$INSTDIR"
    Delete "$SMPROGRAMS\\${APP_NAME}\\*.*"
    RMDir "$SMPROGRAMS\\${APP_NAME}"
    Delete "$DESKTOP\\${APP_NAME}.lnk"
    
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}"
    DeleteRegKey HKLM "Software\\${APP_NAME}"
SectionEnd
"""

    with open("installer.nsi", "w") as f:
        f.write(nsis_script.strip())

    print("Created NSIS installer script")
    print("To build installer, run: makensis installer.nsi")


def main():
    """Main build function"""
    print("Windows Driver Updater - Build Script")
    print("=" * 40)

    # Check PyInstaller
    if not check_pyinstaller():
        print("PyInstaller not found. Installing...")
        if not install_pyinstaller():
            print("ERROR: Failed to install PyInstaller")
            return False

    # Clean previous builds
    clean_build_dirs()

    # Create spec and version files
    create_spec_file()
    create_version_info()

    # Build executable
    if not build_executable():
        return False

    # Copy additional files
    copy_additional_files()

    # Create installer script
    create_installer()

    print("\n" + "=" * 40)
    print("Build completed successfully!")
    print("\nFiles created:")
    print("  - dist/DriverUpdater/ (executable and files)")
    print("  - installer.nsi (NSIS installer script)")
    print("\nTo create installer:")
    print("  1. Install NSIS (https://nsis.sourceforge.io/)")
    print("  2. Run: makensis installer.nsi")

    return True


if __name__ == "__main__":
    success = main()

    if not success:
        print("\nBuild failed. Please check the errors above.")
        input("Press Enter to exit...")
        sys.exit(1)
    else:
        input("\nPress Enter to exit...")
        sys.exit(0)
