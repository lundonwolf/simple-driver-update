"""
Setup script for Windows Driver Updater
Handles initial configuration and dependency verification
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or later is required.")
        print(f"Current version: {sys.version}")
        return False
    return True


def check_windows_version():
    """Check if running on Windows"""
    if sys.platform != "win32":
        print("ERROR: This application only runs on Windows.")
        return False
    return True


def install_dependencies():
    """Install required Python packages"""
    try:
        print("Installing dependencies...")

        # Upgrade pip first
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"]
        )

        # Install requirements
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        )

        # Configure pywin32 after installation
        try:
            print("Configuring pywin32...")
            subprocess.check_call(
                [sys.executable, "-m", "pywin32_postinstall", "-install"]
            )
        except subprocess.CalledProcessError:
            print("Warning: pywin32 configuration may have failed, but continuing...")

        print("Dependencies installed successfully!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        return False


def verify_dependencies():
    """Verify all required modules can be imported"""
    required_modules = [
        "tkinter",
        "requests",
        "psutil",
        "wmi",
        "win32api",
        "beautifulsoup4",
        "packaging",
    ]

    missing_modules = []

    for module in required_modules:
        try:
            if module == "beautifulsoup4":
                import bs4
            elif module == "wmi":
                import wmi  # Try lowercase first
            elif module == "win32api":
                import win32api
            else:
                __import__(module)
            print(f"  ✓ {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"  ✗ {module}")

    if missing_modules:
        print(f"Missing modules: {', '.join(missing_modules)}")
        return False

    print("All dependencies verified!")
    return True


def create_directories():
    """Create necessary directories"""
    directories = ["logs", "temp", "backups", "downloads"]

    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(exist_ok=True)
        print(f"Created directory: {directory}")


def load_config():
    """Load and validate configuration"""
    try:
        with open("config/settings.json", "r") as f:
            config = json.load(f)

        print("Configuration loaded successfully!")
        return config

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR: Failed to load configuration: {e}")
        return None


def check_admin_privileges():
    """Check if running with admin privileges"""
    try:
        import ctypes

        is_admin = ctypes.windll.shell32.IsUserAnAdmin()

        if is_admin:
            print("Running with administrator privileges ✓")
        else:
            print("WARNING: Not running as administrator")
            print("Some features may not work properly")

        return is_admin

    except:
        print("Could not determine admin status")
        return False


def main():
    """Main setup function"""
    print("Windows Driver Updater - Setup")
    print("=" * 40)

    # Check system requirements
    if not check_python_version():
        return False

    if not check_windows_version():
        return False

    # Check admin privileges
    is_admin = check_admin_privileges()

    # Create directories
    create_directories()

    # Load configuration
    config = load_config()
    if not config:
        return False

    # Install/verify dependencies
    if not verify_dependencies():
        print("\nInstalling missing dependencies...")
        if not install_dependencies():
            return False

        # Verify again after installation
        if not verify_dependencies():
            print("ERROR: Dependencies still missing after installation")
            return False

    print("\n" + "=" * 40)
    print("Setup completed successfully!")
    print("\nYou can now run the application using:")
    print("  - run.bat (Windows batch file)")
    print("  - run.ps1 (PowerShell script)")
    print("  - python main.py (direct Python)")

    if not is_admin:
        print("\nIMPORTANT: Run as administrator for full functionality!")

    return True


if __name__ == "__main__":
    success = main()

    if not success:
        print("\nSetup failed. Please check the errors above.")
        input("Press Enter to exit...")
        sys.exit(1)
    else:
        input("\nPress Enter to exit...")
        sys.exit(0)
