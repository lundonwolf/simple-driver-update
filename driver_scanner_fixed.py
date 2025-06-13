import json
import re
import subprocess
from datetime import datetime
from typing import Any, Dict, List

import win32api
import win32con
import wmi


class DriverScanner:
    """Class to scan and analyze system drivers"""

    def __init__(self, logger):
        self.logger = logger
        self.wmi_connection = None
        self.initialize_wmi()

    def initialize_wmi(self):
        """Initialize WMI connection with better error handling"""
        try:
            self.wmi_connection = wmi.WMI()
            self.logger.info("WMI connection initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize WMI connection: {str(e)}")
            self.wmi_connection = None

    def scan_all_drivers(self) -> List[Dict[str, Any]]:
        """Scan all system drivers and return detailed information"""
        self.logger.info("Starting comprehensive driver scan...")

        drivers = []

        try:
            # Get PnP devices and their drivers
            pnp_drivers = self._scan_pnp_drivers()
            drivers.extend(pnp_drivers)

            # Get system drivers
            system_drivers = self._scan_system_drivers()
            drivers.extend(system_drivers)

            # Remove duplicates based on driver file path
            unique_drivers = self._remove_duplicates(drivers)

            self.logger.info(
                f"Driver scan completed. Found {len(unique_drivers)} unique drivers."
            )
            return unique_drivers

        except Exception as e:
            self.logger.error(f"Error during driver scan: {str(e)}")
            raise

    def _scan_pnp_drivers(self) -> List[Dict[str, Any]]:
        """Scan Plug and Play drivers"""
        self.logger.info("Scanning PnP drivers...")
        drivers = []

        if not self.wmi_connection:
            self.logger.warning(
                "WMI connection not available, skipping PnP driver scan"
            )
            return drivers

        try:
            # Query PnP devices
            pnp_entities = self.wmi_connection.Win32_PnPEntity()
            for device in pnp_entities:
                if device.Name and device.DeviceID:
                    driver_info = self._get_driver_info_for_device(device)
                    if driver_info:
                        drivers.append(driver_info)

        except Exception as e:
            self.logger.error(f"Error scanning PnP drivers: {str(e)}")

        self.logger.info(f"Found {len(drivers)} PnP drivers")
        return drivers

    def _scan_system_drivers(self) -> List[Dict[str, Any]]:
        """Scan system drivers with improved error handling"""
        self.logger.info("Scanning system drivers...")
        drivers = []

        if not self.wmi_connection:
            self.logger.warning(
                "WMI connection not available, skipping system driver scan"
            )
            return drivers

        try:
            # Query system drivers with error handling
            system_drivers = self.wmi_connection.Win32_SystemDriver()

            for driver in system_drivers:
                try:
                    if driver.Name and driver.PathName:
                        driver_info = {
                            "device_name": driver.Name,
                            "driver_name": driver.Name,
                            "driver_path": driver.PathName,
                            "version": self._get_file_version(driver.PathName),
                            "date": self._get_file_date(driver.PathName),
                            "status": driver.State or "Unknown",
                            "manufacturer": "Microsoft",  # Most system drivers are Microsoft
                            "device_id": f"SYS_{driver.Name}",
                            "driver_type": "System Driver",
                            "digital_signature": self._check_digital_signature(
                                driver.PathName
                            ),
                        }
                        drivers.append(driver_info)
                except Exception as e:
                    self.logger.warning(
                        f"Error processing system driver {getattr(driver, 'Name', 'Unknown')}: {str(e)}"
                    )
                    continue

        except Exception as e:
            self.logger.error(f"Error scanning system drivers: {str(e)}")
            # Try alternative method using PowerShell/DISM if WMI fails
            try:
                self.logger.info("Attempting alternative driver scan method...")
                alt_drivers = self._scan_drivers_with_powershell()
                drivers.extend(alt_drivers)
            except Exception as alt_e:
                self.logger.error(f"Alternative driver scan also failed: {str(alt_e)}")

        self.logger.info(f"Found {len(drivers)} system drivers")
        return drivers

    def _scan_drivers_with_powershell(self) -> List[Dict[str, Any]]:
        """Alternative driver scanning using PowerShell"""
        self.logger.info("Using PowerShell to scan drivers...")
        drivers = []

        try:
            # Use PowerShell to get driver information
            cmd = [
                "powershell",
                "-Command",
                "Get-WmiObject Win32_PnPSignedDriver | Select-Object DeviceName, DriverVersion, DriverDate, DriverProviderName, Location | ConvertTo-Json",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0 and result.stdout:
                try:
                    driver_data = json.loads(result.stdout)
                    if isinstance(driver_data, list):
                        for driver in driver_data:
                            if driver.get("DeviceName"):
                                driver_info = {
                                    "device_name": driver.get("DeviceName", "Unknown"),
                                    "driver_name": driver.get("DeviceName", "Unknown"),
                                    "driver_path": driver.get("Location", ""),
                                    "version": driver.get("DriverVersion", "Unknown"),
                                    "date": driver.get("DriverDate", "Unknown"),
                                    "status": "Unknown",
                                    "manufacturer": driver.get(
                                        "DriverProviderName", "Unknown"
                                    ),
                                    "device_id": f"PS_{driver.get('DeviceName', 'Unknown')}",
                                    "driver_type": "PowerShell Driver",
                                    "digital_signature": None,
                                }
                                drivers.append(driver_info)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse PowerShell output: {str(e)}")

        except subprocess.TimeoutExpired:
            self.logger.error("PowerShell driver scan timed out")
        except Exception as e:
            self.logger.error(f"PowerShell driver scan failed: {str(e)}")

        return drivers

    def _get_driver_info_for_device(self, device) -> Dict[str, Any]:
        """Get detailed driver information for a specific device"""
        if not self.wmi_connection:
            return None

        try:
            # Try to get associated driver files
            for driver in self.wmi_connection.Win32_PnPSignedDriver():
                if driver.DeviceID == device.DeviceID:
                    driver_info = {
                        "device_name": device.Name or "Unknown Device",
                        "driver_name": driver.DeviceName
                        or driver.DriverName
                        or "Unknown Driver",
                        "driver_path": driver.Location or "",
                        "version": driver.DriverVersion or "Unknown",
                        "date": self._format_driver_date(driver.DriverDate),
                        "status": device.Status or "Unknown",
                        "manufacturer": device.Manufacturer
                        or driver.DriverProviderName
                        or "Unknown",
                        "device_id": device.DeviceID,
                        "driver_type": "PnP Driver",
                        "digital_signature": driver.IsSigned
                        if hasattr(driver, "IsSigned")
                        else None,
                        "hardware_id": device.HardwareID[0]
                        if device.HardwareID
                        else None,
                        "compatible_id": device.CompatibleID[0]
                        if device.CompatibleID
                        else None,
                        "class_guid": device.ClassGuid,
                        "service": device.Service,
                    }
                    return driver_info

            # If no signed driver found, create basic info
            return {
                "device_name": device.Name or "Unknown Device",
                "driver_name": "Unknown Driver",
                "driver_path": "",
                "version": "Unknown",
                "date": "Unknown",
                "status": device.Status or "Unknown",
                "manufacturer": device.Manufacturer or "Unknown",
                "device_id": device.DeviceID,
                "driver_type": "Basic Device Info",
                "digital_signature": None,
                "hardware_id": device.HardwareID[0] if device.HardwareID else None,
                "compatible_id": device.CompatibleID[0]
                if device.CompatibleID
                else None,
                "class_guid": device.ClassGuid,
                "service": device.Service,
            }

        except Exception as e:
            self.logger.error(
                f"Error getting driver info for device {device.Name}: {str(e)}"
            )
            return None

    def _remove_duplicates(self, drivers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate drivers based on device ID and driver path"""
        seen = set()
        unique_drivers = []

        for driver in drivers:
            # Create a unique key based on device_id and driver_path
            key = (driver.get("device_id", ""), driver.get("driver_path", ""))

            if key not in seen:
                seen.add(key)
                unique_drivers.append(driver)

        return unique_drivers

    def _format_driver_date(self, date_str):
        """Format WMI date string to readable format"""
        if not date_str:
            return "Unknown"

        try:
            # WMI date format: 20210301000000.000000-000
            if len(date_str) >= 8:
                year = date_str[:4]
                month = date_str[4:6]
                day = date_str[6:8]
                return f"{year}-{month}-{day}"
        except Exception:
            pass

        return date_str or "Unknown"

    def _get_file_version(self, file_path):
        """Get file version using Windows API"""
        if not file_path:
            return "Unknown"

        try:
            # Clean the path
            if file_path.startswith("\\??\\"):
                file_path = file_path[4:]

            if file_path.startswith("\\SystemRoot\\"):
                import os

                file_path = file_path.replace(
                    "\\SystemRoot\\", os.environ["SystemRoot"] + "\\"
                )

            # Get file version info
            try:
                info = win32api.GetFileVersionInfo(file_path, "\\")
                ms = info["FileVersionMS"]
                ls = info["FileVersionLS"]
                version = f"{win32api.HIWORD(ms)}.{win32api.LOWORD(ms)}.{win32api.HIWORD(ls)}.{win32api.LOWORD(ls)}"
                return version
            except Exception:
                # Alternative method using subprocess
                return self._get_version_with_powershell(file_path)

        except Exception as e:
            self.logger.debug(f"Could not get version for {file_path}: {str(e)}")
            return "Unknown"

    def _get_version_with_powershell(self, file_path):
        """Get file version using PowerShell"""
        try:
            cmd = [
                "powershell",
                "-Command",
                f"(Get-ItemProperty '{file_path}').VersionInfo.FileVersion",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
        return "Unknown"

    def _get_file_date(self, file_path):
        """Get file modification date"""
        if not file_path:
            return "Unknown"

        try:
            # Clean the path
            if file_path.startswith("\\??\\"):
                file_path = file_path[4:]

            if file_path.startswith("\\SystemRoot\\"):
                import os

                file_path = file_path.replace(
                    "\\SystemRoot\\", os.environ["SystemRoot"] + "\\"
                )

            import os

            if os.path.exists(file_path):
                import time

                timestamp = os.path.getmtime(file_path)
                return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")

        except Exception as e:
            self.logger.debug(f"Could not get date for {file_path}: {str(e)}")

        return "Unknown"

    def _check_digital_signature(self, file_path):
        """Check if file has valid digital signature"""
        if not file_path:
            return None

        try:
            # Clean the path
            if file_path.startswith("\\??\\"):
                file_path = file_path[4:]

            if file_path.startswith("\\SystemRoot\\"):
                import os

                file_path = file_path.replace(
                    "\\SystemRoot\\", os.environ["SystemRoot"] + "\\"
                )

            # Use PowerShell to check signature
            cmd = [
                "powershell",
                "-Command",
                f"(Get-AuthenticodeSignature '{file_path}').Status",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                status = result.stdout.strip()
                return status == "Valid"

        except Exception as e:
            self.logger.debug(f"Could not check signature for {file_path}: {str(e)}")

        return None

    def get_driver_categories(
        self, drivers: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize drivers by type"""
        categories = {
            "Graphics": [],
            "Audio": [],
            "Network": [],
            "Storage": [],
            "Input": [],
            "System": [],
            "Other": [],
        }

        for driver in drivers:
            device_name = driver.get("device_name", "").lower()
            hardware_id = (
                driver.get("hardware_id", "").lower()
                if driver.get("hardware_id")
                else ""
            )

            # Categorize based on device name and hardware ID
            if any(
                keyword in device_name or keyword in hardware_id
                for keyword in [
                    "display",
                    "graphics",
                    "video",
                    "nvidia",
                    "amd",
                    "intel hd",
                    "radeon",
                ]
            ):
                categories["Graphics"].append(driver)
            elif any(
                keyword in device_name or keyword in hardware_id
                for keyword in [
                    "audio",
                    "sound",
                    "speaker",
                    "microphone",
                    "realtek",
                    "hdmi audio",
                ]
            ):
                categories["Audio"].append(driver)
            elif any(
                keyword in device_name or keyword in hardware_id
                for keyword in [
                    "network",
                    "ethernet",
                    "wifi",
                    "wireless",
                    "bluetooth",
                    "lan",
                ]
            ):
                categories["Network"].append(driver)
            elif any(
                keyword in device_name or keyword in hardware_id
                for keyword in [
                    "storage",
                    "disk",
                    "ssd",
                    "hdd",
                    "sata",
                    "nvme",
                    "usb mass",
                ]
            ):
                categories["Storage"].append(driver)
            elif any(
                keyword in device_name or keyword in hardware_id
                for keyword in ["keyboard", "mouse", "hid", "input", "touchpad"]
            ):
                categories["Input"].append(driver)
            elif any(
                keyword in device_name or keyword in hardware_id
                for keyword in [
                    "system",
                    "chipset",
                    "acpi",
                    "pci",
                    "usb root",
                    "processor",
                ]
            ):
                categories["System"].append(driver)
            else:
                categories["Other"].append(driver)

        return categories

    def save_driver_report(self, drivers: List[Dict[str, Any]], output_path: str):
        """Save driver scan results to JSON file"""
        try:
            report = {
                "scan_date": datetime.now().isoformat(),
                "total_drivers": len(drivers),
                "drivers": drivers,
                "categories": self.get_driver_categories(drivers),
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Driver report saved to {output_path}")

        except Exception as e:
            self.logger.error(f"Failed to save driver report: {str(e)}")
            raise
