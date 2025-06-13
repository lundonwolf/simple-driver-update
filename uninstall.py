"""
Uninstaller for Windows Driver Updater
Removes application files and cleans up system
"""

import os
import shutil
import sys
import winreg
from pathlib import Path


def remove_registry_entries():
    """Remove registry entries created by the application"""
    print("Removing registry entries...")

    reg_paths = [
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Windows Driver Updater",
        ),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Windows Driver Updater"),
        (winreg.HKEY_CURRENT_USER, r"Software\Windows Driver Updater"),
    ]

    for hkey, path in reg_paths:
        try:
            winreg.DeleteKey(hkey, path)
            print(f"  ✓ Removed: {path}")
        except FileNotFoundError:
            # Key doesn't exist, which is fine
            pass
        except Exception as e:
            print(f"  ✗ Failed to remove {path}: {e}")


def remove_shortcuts():
    """Remove desktop and start menu shortcuts"""
    print("Removing shortcuts...")

    shortcuts = [
        os.path.expanduser("~/Desktop/Windows Driver Updater.lnk"),
        os.path.expanduser(
            "~/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Windows Driver Updater.lnk"
        ),
        os.path.expandvars(
            "%ALLUSERSPROFILE%/Microsoft/Windows/Start Menu/Programs/Windows Driver Updater.lnk"
        ),
    ]

    for shortcut in shortcuts:
        try:
            if os.path.exists(shortcut):
                os.remove(shortcut)
                print(f"  ✓ Removed: {shortcut}")
        except Exception as e:
            print(f"  ✗ Failed to remove {shortcut}: {e}")


def remove_application_data():
    """Remove application data directories"""
    print("Removing application data...")

    data_dirs = [
        os.path.expandvars("%LOCALAPPDATA%\\DriverUpdater"),
        os.path.expandvars("%APPDATA%\\DriverUpdater"),
        os.path.expanduser("~/Documents/DriverUpdater"),
    ]

    for data_dir in data_dirs:
        try:
            if os.path.exists(data_dir):
                shutil.rmtree(data_dir)
                print(f"  ✓ Removed: {data_dir}")
        except Exception as e:
            print(f"  ✗ Failed to remove {data_dir}: {e}")


def remove_temp_files():
    """Remove temporary files"""
    print("Removing temporary files...")

    temp_dirs = [
        os.path.expandvars("%TEMP%\\DriverUpdater"),
        os.path.expandvars("%TEMP%\\driver_updater_*"),
    ]

    for temp_pattern in temp_dirs:
        try:
            import glob

            for temp_dir in glob.glob(temp_pattern):
                if os.path.exists(temp_dir):
                    if os.path.isdir(temp_dir):
                        shutil.rmtree(temp_dir)
                    else:
                        os.remove(temp_dir)
                    print(f"  ✓ Removed: {temp_dir}")
        except Exception as e:
            print(f"  ✗ Failed to remove temp files: {e}")


def remove_installation_directory():
    """Remove the installation directory"""
    print("Removing installation directory...")

    # Get the directory where this script is located
    install_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(install_dir)

    print(f"Installation directory: {install_dir}")

    # Ask for confirmation
    response = input(
        "Are you sure you want to remove the installation directory? (y/N): "
    )
    if response.lower() != "y":
        print("Skipping installation directory removal.")
        return

    try:
        # Move to parent directory before removal
        os.chdir(parent_dir)

        # Remove installation directory
        shutil.rmtree(install_dir)
        print(f"  ✓ Removed installation directory: {install_dir}")

    except Exception as e:
        print(f"  ✗ Failed to remove installation directory: {e}")
        print("You may need to manually delete the directory after reboot.")


def stop_running_processes():
    """Stop any running Driver Updater processes"""
    print("Stopping running processes...")

    try:
        import psutil

        processes_killed = 0
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            try:
                if proc.info["name"] and "driverupdater" in proc.info["name"].lower():
                    proc.terminate()
                    proc.wait(timeout=5)
                    processes_killed += 1
                    print(
                        f"  ✓ Stopped process: {proc.info['name']} (PID: {proc.info['pid']})"
                    )
            except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                pass

        if processes_killed == 0:
            print("  No running processes found.")

    except ImportError:
        print("  psutil not available, skipping process check.")
    except Exception as e:
        print(f"  Error stopping processes: {e}")


def main():
    """Main uninstaller function"""
    print("Windows Driver Updater - Uninstaller")
    print("=" * 40)

    # Confirm uninstallation
    print("This will completely remove Windows Driver Updater from your system.")
    print("This includes:")
    print("  - Application files")
    print("  - Configuration files")
    print("  - Log files")
    print("  - Backup files")
    print("  - Registry entries")
    print("  - Shortcuts")
    print()

    response = input("Do you want to continue? (y/N): ")
    if response.lower() != "y":
        print("Uninstallation cancelled.")
        return

    print("\nStarting uninstallation...")

    # Stop running processes
    stop_running_processes()

    # Remove shortcuts
    remove_shortcuts()

    # Remove application data
    remove_application_data()

    # Remove temporary files
    remove_temp_files()

    # Remove registry entries
    remove_registry_entries()

    # Remove installation directory (last)
    remove_installation_directory()

    print("\n" + "=" * 40)
    print("Uninstallation completed!")
    print("\nWindows Driver Updater has been removed from your system.")
    print("You may need to restart your computer to complete the removal.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nUninstallation cancelled by user.")
    except Exception as e:
        print(f"\nUninstallation failed: {e}")
        import traceback

        traceback.print_exc()

    input("\nPress Enter to exit...")
    sys.exit(0)
