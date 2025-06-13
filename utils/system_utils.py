import ctypes
import os
import subprocess
import sys
import winreg
from datetime import datetime
from typing import List, Optional


class SystemUtils:
    """System utility functions for Windows"""

    def __init__(self, logger):
        self.logger = logger

    def is_admin(self) -> bool:
        """Check if running with administrator privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def elevate_privileges(self):
        """Restart application with administrator privileges"""
        if self.is_admin():
            return True

        try:
            # Re-run the current script with admin privileges
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            return True
        except:
            return False

    def create_restore_point(
        self, description: str = "Driver Updater Checkpoint"
    ) -> bool:
        """Create a system restore point"""
        try:
            self.logger.info(f"Creating system restore point: {description}")

            # PowerShell command to create restore point
            powershell_script = f"""
            Checkpoint-Computer -Description "{description}" -RestorePointType "MODIFY_SETTINGS"
            """

            result = subprocess.run(
                ["powershell", "-Command", powershell_script],
                capture_output=True,
                text=True,
                timeout=120,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            if result.returncode == 0:
                self.logger.info("System restore point created successfully")
                return True
            else:
                self.logger.error(f"Failed to create restore point: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error("Timeout creating restore point")
            return False
        except Exception as e:
            self.logger.error(f"Error creating restore point: {str(e)}")
            return False

    def get_system_info(self) -> dict:
        """Get detailed system information"""
        try:
            info = {}

            # Operating System info
            result = subprocess.run(
                [
                    "wmic",
                    "os",
                    "get",
                    "Caption,Version,BuildNumber,Architecture",
                    "/format:csv",
                ],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    # Parse CSV output (skip header)
                    for line in lines[1:]:
                        if line.strip():
                            fields = line.split(",")
                            if len(fields) >= 5:
                                info["os_architecture"] = fields[1].strip()
                                info["os_build"] = fields[2].strip()
                                info["os_name"] = fields[3].strip()
                                info["os_version"] = fields[4].strip()
                                break

            # Computer info
            result = subprocess.run(
                [
                    "wmic",
                    "computersystem",
                    "get",
                    "TotalPhysicalMemory,Manufacturer,Model",
                    "/format:csv",
                ],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    for line in lines[1:]:
                        if line.strip():
                            fields = line.split(",")
                            if len(fields) >= 4:
                                info["manufacturer"] = fields[1].strip()
                                info["model"] = fields[2].strip()
                                memory_bytes = fields[3].strip()
                                if memory_bytes.isdigit():
                                    info["total_memory_gb"] = round(
                                        int(memory_bytes) / (1024**3), 2
                                    )
                                break

            # Processor info
            result = subprocess.run(
                [
                    "wmic",
                    "cpu",
                    "get",
                    "Name,Manufacturer,MaxClockSpeed",
                    "/format:csv",
                ],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    for line in lines[1:]:
                        if line.strip():
                            fields = line.split(",")
                            if len(fields) >= 4:
                                info["cpu_manufacturer"] = fields[1].strip()
                                info["cpu_max_speed"] = fields[2].strip()
                                info["cpu_name"] = fields[3].strip()
                                break

            return info

        except Exception as e:
            self.logger.error(f"Error getting system info: {str(e)}")
            return {}

    def check_pending_reboot(self) -> bool:
        """Check if system has pending reboot"""
        try:
            # Check various registry locations for pending reboot
            reboot_required = False

            # Check Windows Update reboot required
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired",
                )
                winreg.CloseKey(key)
                reboot_required = True
            except FileNotFoundError:
                pass

            # Check Component Based Servicing reboot required
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending",
                )
                winreg.CloseKey(key)
                reboot_required = True
            except FileNotFoundError:
                pass

            # Check Session Manager reboot required
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SYSTEM\CurrentControlSet\Control\Session Manager",
                )
                value, _ = winreg.QueryValueEx(key, "PendingFileRenameOperations")
                winreg.CloseKey(key)
                if value:
                    reboot_required = True
            except (FileNotFoundError, OSError):
                pass

            return reboot_required

        except Exception as e:
            self.logger.error(f"Error checking pending reboot: {str(e)}")
            return False

    def get_windows_version(self) -> str:
        """Get Windows version string"""
        try:
            result = subprocess.run(
                ["ver"],
                capture_output=True,
                text=True,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass

        return "Unknown"

    def is_windows_10_or_later(self) -> bool:
        """Check if running Windows 10 or later"""
        try:
            import platform

            version = platform.version()
            # Windows 10 build numbers start from 10240
            build_number = int(version.split(".")[-1])
            return build_number >= 10240
        except:
            return False

    def get_installed_updates(self) -> List[str]:
        """Get list of installed Windows updates"""
        try:
            updates = []

            powershell_script = """
            Get-HotFix | Select-Object -Property HotFixID, Description, InstalledOn | 
            Sort-Object InstalledOn -Descending | 
            ForEach-Object { "$($_.HotFixID)|$($_.Description)|$($_.InstalledOn)" }
            """

            result = subprocess.run(
                ["powershell", "-Command", powershell_script],
                capture_output=True,
                text=True,
                timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line.strip() and "|" in line:
                        parts = line.split("|")
                        if len(parts) >= 3:
                            updates.append(
                                {
                                    "id": parts[0].strip(),
                                    "description": parts[1].strip(),
                                    "installed_on": parts[2].strip(),
                                }
                            )

            return updates

        except Exception as e:
            self.logger.error(f"Error getting installed updates: {str(e)}")
            return []

    def check_disk_space(self, path: str = "C:\\") -> dict:
        """Check available disk space"""
        try:
            free_bytes = ctypes.c_ulonglong(0)
            total_bytes = ctypes.c_ulonglong(0)

            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(path),
                ctypes.pointer(free_bytes),
                ctypes.pointer(total_bytes),
                None,
            )

            free_gb = free_bytes.value / (1024**3)
            total_gb = total_bytes.value / (1024**3)
            used_gb = total_gb - free_gb

            return {
                "path": path,
                "free_gb": round(free_gb, 2),
                "total_gb": round(total_gb, 2),
                "used_gb": round(used_gb, 2),
                "free_percent": round((free_gb / total_gb) * 100, 1),
            }

        except Exception as e:
            self.logger.error(f"Error checking disk space: {str(e)}")
            return {}

    def run_system_file_checker(self) -> bool:
        """Run System File Checker (sfc /scannow)"""
        try:
            self.logger.info("Running System File Checker...")

            result = subprocess.run(
                ["sfc", "/scannow"],
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minutes
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            if result.returncode == 0:
                self.logger.info("System File Checker completed successfully")
                return True
            else:
                self.logger.error(f"System File Checker failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error("System File Checker timeout")
            return False
        except Exception as e:
            self.logger.error(f"Error running System File Checker: {str(e)}")
            return False

    def enable_system_restore(self) -> bool:
        """Enable System Restore on C: drive"""
        try:
            self.logger.info("Enabling System Restore...")

            powershell_script = """
            Enable-ComputerRestore -Drive "C:\\"
            """

            result = subprocess.run(
                ["powershell", "-Command", powershell_script],
                capture_output=True,
                text=True,
                timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            if result.returncode == 0:
                self.logger.info("System Restore enabled successfully")
                return True
            else:
                self.logger.error(f"Failed to enable System Restore: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Error enabling System Restore: {str(e)}")
            return False

    def get_system_uptime(self) -> str:
        """Get system uptime"""
        try:
            result = subprocess.run(
                ["wmic", "os", "get", "LastBootUpTime", "/format:csv"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                for line in lines[1:]:
                    if line.strip():
                        fields = line.split(",")
                        if len(fields) >= 2:
                            boot_time_str = fields[1].strip()
                            if boot_time_str:
                                # Parse WMI datetime format
                                boot_time = datetime.strptime(
                                    boot_time_str[:14], "%Y%m%d%H%M%S"
                                )
                                uptime = datetime.now() - boot_time

                                days = uptime.days
                                hours, remainder = divmod(uptime.seconds, 3600)
                                minutes, _ = divmod(remainder, 60)

                                return f"{days} days, {hours} hours, {minutes} minutes"

        except Exception as e:
            self.logger.error(f"Error getting system uptime: {str(e)}")

        return "Unknown"
