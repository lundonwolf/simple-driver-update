"""
Test script for Windows Driver Updater
Performs basic functionality tests without making system changes
"""

import os
import sys
import traceback
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Test all required imports"""
    print("Testing imports...")

    try:
        import tkinter

        print("  ✓ tkinter")
    except ImportError as e:
        print(f"  ✗ tkinter: {e}")
        return False

    try:
        import requests

        print("  ✓ requests")
    except ImportError as e:
        print(f"  ✗ requests: {e}")
        return False

    try:
        import psutil

        print("  ✓ psutil")
    except ImportError as e:
        print(f"  ✗ psutil: {e}")
        return False

    try:
        import wmi

        print("  ✓ wmi")
    except ImportError as e:
        print(f"  ✗ wmi: {e}")
        return False

    try:
        import win32api

        print("  ✓ win32api")
    except ImportError as e:
        print(f"  ✗ win32api: {e}")
        return False

    try:
        from bs4 import BeautifulSoup

        print("  ✓ beautifulsoup4")
    except ImportError as e:
        print(f"  ✗ beautifulsoup4: {e}")
        return False

    try:
        from packaging import version

        print("  ✓ packaging")
    except ImportError as e:
        print(f"  ✗ packaging: {e}")
        return False

    return True


def test_modules():
    """Test custom modules"""
    print("\nTesting custom modules...")

    try:
        from utils.logger import Logger

        logger = Logger()
        logger.info("Logger test")
        print("  ✓ Logger")
    except Exception as e:
        print(f"  ✗ Logger: {e}")
        return False

    try:
        from utils.system_utils import SystemUtils

        system_utils = SystemUtils(logger)
        is_admin = system_utils.is_admin()
        print(f"  ✓ SystemUtils (Admin: {is_admin})")
    except Exception as e:
        print(f"  ✗ SystemUtils: {e}")
        return False

    try:
        from driver_scanner import DriverScanner

        scanner = DriverScanner(logger)
        print("  ✓ DriverScanner")
    except Exception as e:
        print(f"  ✗ DriverScanner: {e}")
        return False

    try:
        from update_checker import UpdateChecker

        checker = UpdateChecker(logger)
        print("  ✓ UpdateChecker")
    except Exception as e:
        print(f"  ✗ UpdateChecker: {e}")
        return False

    try:
        from driver_installer import DriverInstaller

        installer = DriverInstaller(logger)
        print("  ✓ DriverInstaller")
    except Exception as e:
        print(f"  ✗ DriverInstaller: {e}")
        return False

    return True


def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")

    try:
        import json

        config_path = Path("config/settings.json")

        if not config_path.exists():
            print("  ✗ Configuration file not found")
            return False

        with open(config_path, "r") as f:
            config = json.load(f)

        required_sections = ["application", "update_checker", "installer", "logging"]
        for section in required_sections:
            if section not in config:
                print(f"  ✗ Missing config section: {section}")
                return False

        print("  ✓ Configuration loaded successfully")
        return True

    except Exception as e:
        print(f"  ✗ Configuration error: {e}")
        return False


def test_directories():
    """Test directory structure"""
    print("\nTesting directory structure...")

    required_dirs = ["utils", "config"]
    required_files = [
        "main.py",
        "driver_scanner.py",
        "update_checker.py",
        "driver_installer.py",
        "requirements.txt",
        "README.md",
    ]

    # Check directories
    for dir_name in required_dirs:
        if not os.path.isdir(dir_name):
            print(f"  ✗ Missing directory: {dir_name}")
            return False
        print(f"  ✓ Directory: {dir_name}")

    # Check files
    for file_name in required_files:
        if not os.path.isfile(file_name):
            print(f"  ✗ Missing file: {file_name}")
            return False
        print(f"  ✓ File: {file_name}")

    return True


def test_gui_creation():
    """Test GUI creation without showing window"""
    print("\nTesting GUI creation...")

    try:
        import tkinter as tk
        from tkinter import ttk

        # Create root window but don't show it
        root = tk.Tk()
        root.withdraw()  # Hide window

        # Test basic widgets
        frame = ttk.Frame(root)
        label = ttk.Label(frame, text="Test")
        button = ttk.Button(frame, text="Test")

        # Destroy window
        root.destroy()

        print("  ✓ GUI components created successfully")
        return True

    except Exception as e:
        print(f"  ✗ GUI creation failed: {e}")
        return False


def test_wmi_connection():
    """Test WMI connection"""
    print("\nTesting WMI connection...")

    try:
        import wmi

        c = wmi.WMI()

        # Simple query to test connection
        os_info = list(c.Win32_OperatingSystem())
        if os_info:
            print(f"  ✓ WMI connected (OS: {os_info[0].Caption})")
            return True
        else:
            print("  ✗ WMI query returned no results")
            return False

    except Exception as e:
        print(f"  ✗ WMI connection failed: {e}")
        return False


def main():
    """Run all tests"""
    print("Windows Driver Updater - Test Suite")
    print("=" * 40)

    tests = [
        ("Imports", test_imports),
        ("Directory Structure", test_directories),
        ("Configuration", test_config),
        ("Custom Modules", test_modules),
        ("GUI Creation", test_gui_creation),
        ("WMI Connection", test_wmi_connection),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"\n{test_name} test FAILED")
        except Exception as e:
            print(f"\n{test_name} test FAILED with exception: {e}")
            traceback.print_exc()

    print("\n" + "=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All tests passed! The application should work correctly.")
        return True
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = main()

    print("\nPress Enter to exit...")
    input()

    sys.exit(0 if success else 1)
