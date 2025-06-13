import json
import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from packaging import version


class UpdateChecker:
    """Class to check for driver updates from manufacturer websites"""

    def __init__(self, logger):
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

        # Enhanced features
        self.relaxed_validation = False
        self.verbose_mode = False
        self.progress_callback = None

        # Manufacturer-specific update checkers
        self.update_checkers = {
            "nvidia": self._check_nvidia_updates,
            "amd": self._check_amd_updates,
            "intel": self._check_intel_updates,
            "realtek": self._check_realtek_updates,
            "microsoft": self._check_microsoft_updates,
            "generic": self._check_generic_updates,
        }

        # Common manufacturer URLs
        self.manufacturer_urls = {
            "nvidia": "https://www.nvidia.com/drivers/",
            "amd": "https://www.amd.com/support/",
            "intel": "https://downloadcenter.intel.com/",
            "realtek": "https://www.realtek.com/downloads/",
            "microsoft": "https://catalog.update.microsoft.com/",
        }

    def set_relaxed_validation(self, enabled):
        """Enable or disable relaxed validation"""
        self.relaxed_validation = enabled
        if self.verbose_mode:
            self.logger.info(
                f"Relaxed validation: {'enabled' if enabled else 'disabled'}"
            )

    def set_verbose_mode(self, enabled):
        """Enable or disable verbose mode"""
        self.verbose_mode = enabled

    def check_for_updates(
        self, drivers_data: List[Dict[str, Any]], progress_callback=None
    ) -> List[Dict[str, Any]]:
        """Enhanced update checking with progress callbacks"""
        self.progress_callback = progress_callback

        if self.verbose_mode:
            self.logger.info(
                f"Enhanced update check starting for {len(drivers_data)} drivers"
            )
            self.logger.info(f"Relaxed validation: {self.relaxed_validation}")

        updates_available = []

        for i, driver in enumerate(drivers_data):
            try:
                if self.progress_callback:
                    self.progress_callback(
                        i + 1, len(drivers_data), driver.get("device_name", "Unknown")
                    )

                if self.verbose_mode:
                    self.logger.info(
                        f"Checking updates for driver {i+1}/{len(drivers_data)}: {driver.get('device_name', 'Unknown')}"
                    )

                update_info = self._check_driver_update(driver)
                if update_info:
                    updates_available.append(update_info)
                    if self.verbose_mode:
                        self.logger.info(
                            f"  ✅ Update found: {update_info.get('new_version', 'Unknown version')}"
                        )
                elif self.verbose_mode:
                    self.logger.info(f"  ℹ️ No update available")

                # Reduced delay for better user experience
                time.sleep(0.5)

            except Exception as e:
                if self.verbose_mode:
                    self.logger.error(
                        f"  ❌ Error checking {driver.get('device_name', 'Unknown')}: {str(e)}"
                    )
                else:
                    self.logger.error(
                        f"Error checking updates for {driver.get('device_name', 'Unknown')}: {str(e)}"
                    )

                # In relaxed mode, continue even with errors
                if self.relaxed_validation:
                    continue
                else:
                    # In strict mode, you might want to stop or handle differently
                    continue

        if self.verbose_mode:
            self.logger.info(
                f"Enhanced update check completed. Found {len(updates_available)} updates."
            )

        return updates_available

    def _check_driver_update(self, driver: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for updates for a specific driver"""
        manufacturer = driver.get("manufacturer", "").lower()
        device_name = driver.get("device_name", "")
        hardware_id = driver.get("hardware_id", "")
        current_version = driver.get("version", "")

        # Determine manufacturer-specific checker
        checker_func = None
        for mfg_key, checker in self.update_checkers.items():
            if mfg_key in manufacturer or mfg_key in device_name.lower():
                checker_func = checker
                break

        if not checker_func:
            checker_func = self.update_checkers["generic"]

        try:
            return checker_func(driver)
        except Exception as e:
            self.logger.error(f"Error in manufacturer-specific update check: {str(e)}")
            return None

    def _check_nvidia_updates(self, driver: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for NVIDIA driver updates"""
        device_name = driver.get("device_name", "").lower()

        # Only check for NVIDIA graphics cards
        if (
            "nvidia" not in device_name
            and "geforce" not in device_name
            and "quadro" not in device_name
        ):
            return None

        try:
            # NVIDIA GeForce Experience API or web scraping
            url = "https://www.nvidia.com/Download/processFind.aspx"

            # Extract GPU series from device name
            gpu_series = self._extract_nvidia_gpu_series(device_name)
            if not gpu_series:
                return None

            # Simulate checking for updates (in real implementation, would use NVIDIA API)
            # For demo purposes, return a mock update
            current_version = driver.get("version", "0.0.0.0")
            new_version = self._generate_mock_version(current_version)

            if self._is_version_newer(new_version, current_version):
                return {
                    "device_name": driver.get("device_name"),
                    "current_version": current_version,
                    "new_version": new_version,
                    "download_url": f"https://us.download.nvidia.com/Windows/{new_version}/GeForce_Driver.exe",
                    "download_size": "500 MB",
                    "release_notes": "Bug fixes and performance improvements",
                    "manufacturer": "NVIDIA",
                    "status": "Available",
                    "driver_type": "Graphics",
                }

        except Exception as e:
            self.logger.error(f"Error checking NVIDIA updates: {str(e)}")

        return None

    def _check_amd_updates(self, driver: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for AMD driver updates"""
        device_name = driver.get("device_name", "").lower()

        # Only check for AMD graphics cards
        if (
            "amd" not in device_name
            and "radeon" not in device_name
            and "ati" not in device_name
        ):
            return None

        try:
            # AMD driver detection would go here
            # For demo purposes, return a mock update
            current_version = driver.get("version", "0.0.0.0")
            new_version = self._generate_mock_version(current_version)

            if self._is_version_newer(new_version, current_version):
                return {
                    "device_name": driver.get("device_name"),
                    "current_version": current_version,
                    "new_version": new_version,
                    "download_url": f"https://drivers.amd.com/drivers/installer/22.40/radeon-software-adrenalin-{new_version}.exe",
                    "download_size": "450 MB",
                    "release_notes": "Performance optimizations and bug fixes",
                    "manufacturer": "AMD",
                    "status": "Available",
                    "driver_type": "Graphics",
                }

        except Exception as e:
            self.logger.error(f"Error checking AMD updates: {str(e)}")

        return None

    def _check_intel_updates(self, driver: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for Intel driver updates"""
        device_name = driver.get("device_name", "").lower()

        # Check for Intel devices
        if "intel" not in device_name:
            return None

        try:
            # Intel Driver & Support Assistant API would go here
            # For demo purposes, return a mock update for some Intel devices
            current_version = driver.get("version", "0.0.0.0")
            new_version = self._generate_mock_version(current_version)

            if self._is_version_newer(new_version, current_version):
                return {
                    "device_name": driver.get("device_name"),
                    "current_version": current_version,
                    "new_version": new_version,
                    "download_url": f"https://downloadmirror.intel.com/drivers/{new_version}/intel-driver.exe",
                    "download_size": "200 MB",
                    "release_notes": "Stability improvements and new features",
                    "manufacturer": "Intel",
                    "status": "Available",
                    "driver_type": "System",
                }

        except Exception as e:
            self.logger.error(f"Error checking Intel updates: {str(e)}")

        return None

    def _check_realtek_updates(
        self, driver: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check for Realtek driver updates"""
        device_name = driver.get("device_name", "").lower()

        # Check for Realtek devices
        if "realtek" not in device_name:
            return None

        try:
            # Realtek update checking would go here
            current_version = driver.get("version", "0.0.0.0")
            new_version = self._generate_mock_version(current_version)

            if self._is_version_newer(new_version, current_version):
                return {
                    "device_name": driver.get("device_name"),
                    "current_version": current_version,
                    "new_version": new_version,
                    "download_url": f"https://www.realtek.com/downloads/{new_version}/realtek-driver.exe",
                    "download_size": "50 MB",
                    "release_notes": "Audio and network improvements",
                    "manufacturer": "Realtek",
                    "status": "Available",
                    "driver_type": "Audio/Network",
                }

        except Exception as e:
            self.logger.error(f"Error checking Realtek updates: {str(e)}")

        return None

    def _check_microsoft_updates(
        self, driver: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check for Microsoft driver updates via Windows Update"""
        try:
            # Would integrate with Windows Update API
            # For demo purposes, occasionally return an update
            import random

            if random.random() < 0.1:  # 10% chance of update
                current_version = driver.get("version", "0.0.0.0")
                new_version = self._generate_mock_version(current_version)

                return {
                    "device_name": driver.get("device_name"),
                    "current_version": current_version,
                    "new_version": new_version,
                    "download_url": "windows_update",
                    "download_size": "10 MB",
                    "release_notes": "Windows Update driver package",
                    "manufacturer": "Microsoft",
                    "status": "Available",
                    "driver_type": "System",
                }

        except Exception as e:
            self.logger.error(f"Error checking Microsoft updates: {str(e)}")

        return None

    def _check_generic_updates(
        self, driver: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generic update checker for unknown manufacturers"""
        try:
            # Try to find updates using hardware ID or device name
            hardware_id = driver.get("hardware_id", "")
            device_name = driver.get("device_name", "")

            if hardware_id:
                # Extract vendor and device IDs
                vendor_id, device_id = self._parse_hardware_id(hardware_id)
                if vendor_id and device_id:
                    # Would check PCI database or manufacturer websites
                    pass

            # For demo purposes, occasionally return an update
            import random

            if random.random() < 0.05:  # 5% chance of update
                current_version = driver.get("version", "0.0.0.0")
                new_version = self._generate_mock_version(current_version)

                return {
                    "device_name": driver.get("device_name"),
                    "current_version": current_version,
                    "new_version": new_version,
                    "download_url": "generic_update",
                    "download_size": "25 MB",
                    "release_notes": "Generic driver update",
                    "manufacturer": driver.get("manufacturer", "Unknown"),
                    "status": "Available",
                    "driver_type": "Generic",
                }

        except Exception as e:
            self.logger.error(f"Error in generic update check: {str(e)}")

        return None

    def _extract_nvidia_gpu_series(self, device_name: str) -> Optional[str]:
        """Extract NVIDIA GPU series from device name"""
        patterns = [r"geforce\s+(rtx|gtx)\s+(\d+)", r"quadro\s+(\w+)", r"tesla\s+(\w+)"]

        for pattern in patterns:
            match = re.search(pattern, device_name, re.IGNORECASE)
            if match:
                return match.group(0)

        return None

    def _parse_hardware_id(self, hardware_id: str) -> tuple:
        """Parse hardware ID to extract vendor and device IDs"""
        try:
            # Example: PCI\VEN_10DE&DEV_1234&SUBSYS_...
            match = re.search(
                r"VEN_([0-9A-F]{4})&DEV_([0-9A-F]{4})", hardware_id, re.IGNORECASE
            )
            if match:
                return match.group(1), match.group(2)
        except:
            pass

        return None, None

    def _generate_mock_version(self, current_version: str) -> str:
        """Generate a mock newer version for demonstration"""
        try:
            # Parse current version
            parts = current_version.split(".")
            if len(parts) >= 2:
                major = int(parts[0])
                minor = int(parts[1])
                build = int(parts[2]) if len(parts) > 2 else 0
                revision = int(parts[3]) if len(parts) > 3 else 0

                # Increment build number
                build += 1

                return f"{major}.{minor}.{build}.{revision}"

        except:
            pass

        return "1.0.0.1"

    def _is_version_newer(self, new_version: str, current_version: str) -> bool:
        """Compare versions to determine if new version is newer"""
        try:
            return version.parse(new_version) > version.parse(current_version)
        except:
            # Fallback comparison
            try:
                new_parts = [int(x) for x in new_version.split(".")]
                current_parts = [int(x) for x in current_version.split(".")]

                # Pad shorter version with zeros
                max_len = max(len(new_parts), len(current_parts))
                new_parts.extend([0] * (max_len - len(new_parts)))
                current_parts.extend([0] * (max_len - len(current_parts)))

                return new_parts > current_parts
            except:
                return False

    def download_driver(self, update_info: Dict[str, Any], download_path: str) -> bool:
        """Download a driver update"""
        try:
            download_url = update_info.get("download_url")
            if not download_url or download_url in ["windows_update", "generic_update"]:
                return False

            self.logger.info(f"Downloading driver from {download_url}")

            response = self.session.get(download_url, stream=True)
            response.raise_for_status()

            with open(download_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            self.logger.info(f"Driver downloaded successfully to {download_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error downloading driver: {str(e)}")
            return False

    def verify_download(self, file_path: str, expected_size: str = None) -> bool:
        """Verify downloaded driver file"""
        try:
            import os

            if not os.path.exists(file_path):
                return False

            file_size = os.path.getsize(file_path)

            # Basic size check
            if expected_size:
                # Convert expected size to bytes (rough estimate)
                expected_bytes = self._parse_size_string(expected_size)
                if (
                    expected_bytes
                    and abs(file_size - expected_bytes) > expected_bytes * 0.1
                ):  # 10% tolerance
                    return False

            # Check if file is executable
            if not file_path.lower().endswith((".exe", ".msi", ".inf")):
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error verifying download: {str(e)}")
            return False

    def _parse_size_string(self, size_str: str) -> Optional[int]:
        """Parse size string like '500 MB' to bytes"""
        try:
            match = re.search(r"(\d+(?:\.\d+)?)\s*(KB|MB|GB)", size_str, re.IGNORECASE)
            if match:
                size = float(match.group(1))
                unit = match.group(2).upper()

                multipliers = {"KB": 1024, "MB": 1024**2, "GB": 1024**3}
                return int(size * multipliers.get(unit, 1))

        except:
            pass

        return None
