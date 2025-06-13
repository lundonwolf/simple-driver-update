import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class DriverInstaller:
    """Class to handle driver installation"""

    def __init__(self, logger):
        self.logger = logger
        self.temp_dir = tempfile.mkdtemp(prefix="driver_updater_")
        self.backup_dir = os.path.join(self.temp_dir, "driver_backups")
        os.makedirs(self.backup_dir, exist_ok=True)

        # Enhanced features
        self.verbose_mode = False
        self.interactive_mode = False

    def set_verbose_mode(self, enabled):
        """Enable or disable verbose mode"""
        self.verbose_mode = enabled

    def set_interactive_mode(self, enabled):
        """Enable or disable interactive mode"""
        self.interactive_mode = enabled

    def install_updates(self, updates: List[Dict[str, Any]]) -> int:
        """Install all available driver updates"""
        self.logger.info(f"Starting installation of {len(updates)} driver updates...")

        success_count = 0

        # Create system restore point before installation
        from utils.system_utils import SystemUtils

        system_utils = SystemUtils(self.logger)
        restore_point_created = system_utils.create_restore_point(
            "Driver Updater - Batch Installation"
        )

        if not restore_point_created:
            self.logger.warning(
                "Failed to create restore point, but continuing with installation"
            )

        for i, update in enumerate(updates):
            try:
                self.logger.info(
                    f"Installing update {i+1}/{len(updates)}: {update.get('device_name', 'Unknown')}"
                )

                if self._install_single_update(update):
                    success_count += 1
                    self.logger.info(
                        f"Successfully installed update for {update.get('device_name', 'Unknown')}"
                    )
                else:
                    self.logger.error(
                        f"Failed to install update for {update.get('device_name', 'Unknown')}"
                    )

            except Exception as e:
                self.logger.error(
                    f"Error installing update for {update.get('device_name', 'Unknown')}: {str(e)}"
                )
                continue

        self.logger.info(
            f"Installation completed. {success_count}/{len(updates)} updates installed successfully."
        )
        return success_count

    def _install_single_update(self, update: Dict[str, Any]) -> bool:
        """Install a single driver update"""
        try:
            download_url = update.get("download_url")
            device_name = update.get("device_name", "Unknown")

            if not download_url:
                self.logger.error(f"No download URL for {device_name}")
                return False

            # Handle special cases
            if download_url == "windows_update":
                return self._install_via_windows_update(update)
            elif download_url == "generic_update":
                self.logger.info(
                    f"Generic update for {device_name} - skipping automatic installation"
                )
                return False

            # Download the driver
            driver_file = self._download_driver(update)
            if not driver_file:
                return False

            # Create backup of current driver
            self._backup_current_driver(update)

            # Install the driver
            return self._install_driver_file(driver_file, update)

        except Exception as e:
            self.logger.error(f"Error in single update installation: {str(e)}")
            return False

    def install_single_update_interactive(self, update: Dict[str, Any]) -> bool:
        """Install a single driver update with interactive prompts"""
        try:
            device_name = update.get("device_name", "Unknown")
            download_url = update.get("download_url")

            if self.verbose_mode:
                self.logger.info(
                    f"🔄 Starting interactive installation for: {device_name}"
                )
                self.logger.info(f"  Download URL: {download_url}")
                self.logger.info(
                    f"  Current version: {update.get('current_version', 'Unknown')}"
                )
                self.logger.info(
                    f"  New version: {update.get('new_version', 'Unknown')}"
                )

            if not download_url:
                if self.verbose_mode:
                    self.logger.error(f"❌ No download URL for {device_name}")
                return False

            # Handle special cases
            if download_url == "windows_update":
                if self.verbose_mode:
                    self.logger.info(f"📥 Installing via Windows Update: {device_name}")
                return self._install_via_windows_update_interactive(update)
            elif download_url == "generic_update":
                if self.verbose_mode:
                    self.logger.info(
                        f"⚠️ Generic update for {device_name} - manual installation recommended"
                    )
                return False

            # Create backup of current driver
            if self.verbose_mode:
                self.logger.info(f"💾 Creating backup for: {device_name}")
            backup_success = self._backup_current_driver(update)

            if backup_success and self.verbose_mode:
                self.logger.info(f"✅ Backup created successfully")
            elif self.verbose_mode:
                self.logger.warning(f"⚠️ Backup creation failed, continuing anyway")

            # Download the driver
            if self.verbose_mode:
                self.logger.info(f"📥 Downloading driver for: {device_name}")
            driver_file = self._download_driver_interactive(update)
            if not driver_file:
                return False

            # Install the driver
            if self.verbose_mode:
                self.logger.info(f"⚡ Installing driver for: {device_name}")
            return self._install_driver_file_interactive(driver_file, update)

        except Exception as e:
            if self.verbose_mode:
                self.logger.error(
                    f"❌ Error in interactive installation for {device_name}: {str(e)}"
                )
            else:
                self.logger.error(f"Error in interactive installation: {str(e)}")
            return False

    def _download_driver(self, update: Dict[str, Any]) -> Optional[str]:
        """Download driver file"""
        try:
            from update_checker import UpdateChecker

            download_url = update.get("download_url")
            device_name = update.get("device_name", "Unknown")

            # Generate filename
            filename = self._generate_driver_filename(update)
            download_path = os.path.join(self.temp_dir, filename)

            # Download using update checker
            update_checker = UpdateChecker(self.logger)
            if update_checker.download_driver(update, download_path):
                # Verify download
                if update_checker.verify_download(
                    download_path, update.get("download_size")
                ):
                    return download_path
                else:
                    self.logger.error(f"Download verification failed for {device_name}")
                    return None
            else:
                self.logger.error(f"Download failed for {device_name}")
                return None

        except Exception as e:
            self.logger.error(f"Error downloading driver: {str(e)}")
            return None

    def _download_driver_interactive(self, update: Dict[str, Any]) -> Optional[str]:
        """Download driver file with interactive progress"""
        device_name = update.get("device_name", "Unknown")
        download_url = update.get("download_url")

        if self.verbose_mode:
            self.logger.info(f"📥 Starting download for {device_name}")
            self.logger.info(f"  URL: {download_url}")

        try:
            response = self.session.get(download_url, stream=True, timeout=30)
            response.raise_for_status()

            # Get file size if available
            total_size = int(response.headers.get("content-length", 0))
            if self.verbose_mode and total_size > 0:
                self.logger.info(f"  File size: {total_size / (1024*1024):.1f} MB")

            # Generate filename
            filename = self._generate_driver_filename(update, response)
            file_path = os.path.join(self.temp_dir, filename)

            # Download with progress
            downloaded = 0
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if self.verbose_mode and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if downloaded % (1024 * 1024) == 0:  # Log every MB
                                self.logger.info(
                                    f"  Progress: {progress:.1f}% ({downloaded / (1024*1024):.1f} MB)"
                                )

            if self.verbose_mode:
                self.logger.info(f"✅ Download completed: {file_path}")

            return file_path

        except Exception as e:
            if self.verbose_mode:
                self.logger.error(f"❌ Download failed for {device_name}: {str(e)}")
            else:
                self.logger.error(f"Download failed: {str(e)}")
            return None

    def _install_driver_file(self, driver_file: str, update: Dict[str, Any]) -> bool:
        """Install driver from file"""
        try:
            device_name = update.get("device_name", "Unknown")
            file_ext = os.path.splitext(driver_file)[1].lower()

            if file_ext == ".exe":
                return self._install_exe_driver(driver_file, update)
            elif file_ext == ".msi":
                return self._install_msi_driver(driver_file, update)
            elif file_ext == ".inf":
                return self._install_inf_driver(driver_file, update)
            else:
                self.logger.error(f"Unsupported driver file type: {file_ext}")
                return False

        except Exception as e:
            self.logger.error(f"Error installing driver file: {str(e)}")
            return False

    def _install_driver_file_interactive(
        self, driver_file: str, update: Dict[str, Any]
    ) -> bool:
        """Install driver file with interactive feedback"""
        device_name = update.get("device_name", "Unknown")

        if self.verbose_mode:
            self.logger.info(f"⚡ Installing driver file: {driver_file}")
            self.logger.info(f"  Device: {device_name}")

        try:
            # Check file type and install accordingly
            file_ext = os.path.splitext(driver_file)[1].lower()

            if file_ext == ".exe":
                return self._install_exe_driver_interactive(driver_file, update)
            elif file_ext == ".msi":
                return self._install_msi_driver_interactive(driver_file, update)
            elif file_ext in [".inf", ".cat", ".sys"]:
                return self._install_inf_driver_interactive(driver_file, update)
            elif file_ext == ".zip":
                return self._install_zip_driver_interactive(driver_file, update)
            else:
                if self.verbose_mode:
                    self.logger.warning(f"⚠️ Unknown driver file type: {file_ext}")
                return False

        except Exception as e:
            if self.verbose_mode:
                self.logger.error(f"❌ Installation failed for {device_name}: {str(e)}")
            else:
                self.logger.error(f"Installation failed: {str(e)}")
            return False

    def _install_exe_driver(self, driver_file: str, update: Dict[str, Any]) -> bool:
        """Install EXE driver package"""
        try:
            device_name = update.get("device_name", "Unknown")

            # Common silent installation parameters
            silent_params = [
                "/S",  # NSIS
                "/SILENT",  # InstallShield
                "/VERYSILENT",  # Inno Setup
                "/q",  # MSI-based
                "/s",  # Generic
                "-s",  # Alternative
                "--silent",  # Alternative
                "/quiet",  # Alternative
            ]

            # Try different silent installation methods
            for param in silent_params:
                try:
                    cmd = [driver_file, param]
                    self.logger.info(f"Attempting installation with parameter: {param}")

                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=300,  # 5 minute timeout
                        creationflags=subprocess.CREATE_NO_WINDOW,
                    )

                    if result.returncode == 0:
                        self.logger.info(
                            f"Successfully installed {device_name} using {param}"
                        )
                        return True
                    elif result.returncode == 3010:  # Reboot required
                        self.logger.info(
                            f"Successfully installed {device_name}, reboot required"
                        )
                        return True

                except subprocess.TimeoutExpired:
                    self.logger.warning(
                        f"Installation timeout for {device_name} with {param}"
                    )
                    continue
                except Exception as e:
                    self.logger.warning(f"Installation failed with {param}: {str(e)}")
                    continue

            # If all silent methods fail, try interactive installation
            self.logger.warning(
                f"Silent installation failed for {device_name}, attempting interactive installation"
            )
            return self._install_interactive(driver_file, update)

        except Exception as e:
            self.logger.error(f"Error installing EXE driver: {str(e)}")
            return False

    def _install_exe_driver_interactive(
        self, driver_file: str, update: Dict[str, Any]
    ) -> bool:
        """Install EXE driver with interactive monitoring"""
        device_name = update.get("device_name", "Unknown")

        if self.verbose_mode:
            self.logger.info(f"🔧 Installing EXE driver for: {device_name}")

        try:
            # Run installer with silent mode
            cmd = [driver_file, "/S", "/silent", "/quiet", "/norestart"]

            if self.verbose_mode:
                self.logger.info(f"  Command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300  # 5 minutes timeout
            )

            if result.returncode == 0:
                if self.verbose_mode:
                    self.logger.info(f"✅ EXE installation completed successfully")
                return True
            else:
                if self.verbose_mode:
                    self.logger.error(
                        f"❌ EXE installation failed with code {result.returncode}"
                    )
                    if result.stderr:
                        self.logger.error(f"  Error output: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            if self.verbose_mode:
                self.logger.error(f"❌ EXE installation timed out after 5 minutes")
            return False
        except Exception as e:
            if self.verbose_mode:
                self.logger.error(f"❌ EXE installation error: {str(e)}")
            return False

    def _install_msi_driver(self, driver_file: str, update: Dict[str, Any]) -> bool:
        """Install MSI driver package"""
        try:
            device_name = update.get("device_name", "Unknown")

            cmd = ["msiexec", "/i", driver_file, "/quiet", "/norestart"]

            self.logger.info(f"Installing MSI driver for {device_name}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            if result.returncode == 0:
                self.logger.info(f"Successfully installed MSI driver for {device_name}")
                return True
            elif result.returncode == 3010:  # Reboot required
                self.logger.info(
                    f"Successfully installed MSI driver for {device_name}, reboot required"
                )
                return True
            else:
                self.logger.error(
                    f"MSI installation failed for {device_name}: {result.stderr}"
                )
                return False

        except Exception as e:
            self.logger.error(f"Error installing MSI driver: {str(e)}")
            return False

    def _install_msi_driver_interactive(
        self, driver_file: str, update: Dict[str, Any]
    ) -> bool:
        """Install MSI driver with interactive monitoring"""
        device_name = update.get("device_name", "Unknown")

        if self.verbose_mode:
            self.logger.info(f"🔧 Installing MSI driver for: {device_name}")

        try:
            # Run installer with silent mode
            cmd = ["msiexec", "/i", driver_file, "/quiet", "/norestart"]

            if self.verbose_mode:
                self.logger.info(f"  Command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300  # 5 minutes timeout
            )

            if result.returncode == 0:
                if self.verbose_mode:
                    self.logger.info(f"✅ MSI installation completed successfully")
                return True
            else:
                if self.verbose_mode:
                    self.logger.error(
                        f"❌ MSI installation failed with code {result.returncode}"
                    )
                    if result.stderr:
                        self.logger.error(f"  Error output: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            if self.verbose_mode:
                self.logger.error(f"❌ MSI installation timed out after 5 minutes")
            return False
        except Exception as e:
            if self.verbose_mode:
                self.logger.error(f"❌ MSI installation error: {str(e)}")
            return False

    def _install_inf_driver(self, driver_file: str, update: Dict[str, Any]) -> bool:
        """Install INF driver package"""
        try:
            device_name = update.get("device_name", "Unknown")

            cmd = ["pnputil", "/add-driver", driver_file, "/install"]

            self.logger.info(f"Installing INF driver for {device_name}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            if result.returncode == 0:
                self.logger.info(f"Successfully installed INF driver for {device_name}")
                return True
            else:
                self.logger.error(
                    f"INF installation failed for {device_name}: {result.stderr}"
                )
                return False

        except Exception as e:
            self.logger.error(f"Error installing INF driver: {str(e)}")
            return False

    def _install_inf_driver_interactive(
        self, driver_file: str, update: Dict[str, Any]
    ) -> bool:
        """Install INF driver with interactive monitoring"""
        device_name = update.get("device_name", "Unknown")

        if self.verbose_mode:
            self.logger.info(f"🔧 Installing INF driver for: {device_name}")

        try:
            # Run installer with silent mode
            cmd = ["pnputil", "/add-driver", driver_file, "/install"]

            if self.verbose_mode:
                self.logger.info(f"  Command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300  # 5 minutes timeout
            )

            if result.returncode == 0:
                if self.verbose_mode:
                    self.logger.info(f"✅ INF installation completed successfully")
                return True
            else:
                if self.verbose_mode:
                    self.logger.error(
                        f"❌ INF installation failed with code {result.returncode}"
                    )
                    if result.stderr:
                        self.logger.error(f"  Error output: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            if self.verbose_mode:
                self.logger.error(f"❌ INF installation timed out after 5 minutes")
            return False
        except Exception as e:
            if self.verbose_mode:
                self.logger.error(f"❌ INF installation error: {str(e)}")
            return False

    def _install_zip_driver_interactive(
        self, driver_file: str, update: Dict[str, Any]
    ) -> bool:
        """Install ZIP driver package with interactive prompts"""
        device_name = update.get("device_name", "Unknown")

        if self.verbose_mode:
            self.logger.info(f"📦 Installing ZIP driver for: {device_name}")

        try:
            # Create temporary directory for extraction
            with tempfile.TemporaryDirectory() as extract_dir:
                self.logger.info(f"  Extracting ZIP file to: {extract_dir}")

                # Extract ZIP file
                shutil.unpack_archive(driver_file, extract_dir)

                # Find and install all drivers in the extracted folder
                for root, _, files in os.walk(extract_dir):
                    for file in files:
                        if file.endswith((".inf", ".sys", ".cat")):
                            file_path = os.path.join(root, file)
                            self.logger.info(f"  Installing driver file: {file_path}")
                            self._install_inf_driver_interactive(file_path, update)

            if self.verbose_mode:
                self.logger.info(f"✅ ZIP driver installation completed")
            return True

        except Exception as e:
            if self.verbose_mode:
                self.logger.error(f"❌ ZIP driver installation error: {str(e)}")
            return False

    def _install_interactive(self, driver_file: str, update: Dict[str, Any]) -> bool:
        """Fallback interactive installation"""
        try:
            device_name = update.get("device_name", "Unknown")

            self.logger.info(f"Starting interactive installation for {device_name}")

            # Start the installer and wait for completion
            result = subprocess.run(
                [driver_file],
                timeout=600,  # 10 minute timeout for interactive
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            # Assume success if installer exits normally
            if result.returncode == 0 or result.returncode == 3010:
                self.logger.info(
                    f"Interactive installation completed for {device_name}"
                )
                return True
            else:
                self.logger.error(f"Interactive installation failed for {device_name}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error(f"Interactive installation timeout for {device_name}")
            return False
        except Exception as e:
            self.logger.error(f"Error in interactive installation: {str(e)}")
            return False

    def _install_via_windows_update(self, update: Dict[str, Any]) -> bool:
        """Install driver via Windows Update"""
        try:
            device_name = update.get("device_name", "Unknown")

            self.logger.info(f"Installing {device_name} via Windows Update")

            # Use PowerShell to trigger Windows Update for specific device
            powershell_script = f"""
            $Session = New-Object -ComObject Microsoft.Update.Session
            $Searcher = $Session.CreateUpdateSearcher()
            $SearchResult = $Searcher.Search("IsInstalled=0 and Type='Driver'")
            
            foreach ($Update in $SearchResult.Updates) {{
                if ($Update.Title -like "*{device_name}*") {{
                    $UpdatesToDownload = New-Object -ComObject Microsoft.Update.UpdateColl
                    $UpdatesToDownload.Add($Update)
                    
                    $Downloader = $Session.CreateUpdateDownloader()
                    $Downloader.Updates = $UpdatesToDownload
                    $Downloader.Download()
                    
                    $UpdatesToInstall = New-Object -ComObject Microsoft.Update.UpdateColl
                    $UpdatesToInstall.Add($Update)
                    
                    $Installer = $Session.CreateUpdateInstaller()
                    $Installer.Updates = $UpdatesToInstall
                    $InstallationResult = $Installer.Install()
                    
                    exit $InstallationResult.ResultCode
                }}
            }}
            exit 1
            """

            result = subprocess.run(
                ["powershell", "-Command", powershell_script],
                capture_output=True,
                text=True,
                timeout=300,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            if result.returncode == 2:  # orcSucceeded
                self.logger.info(
                    f"Successfully installed {device_name} via Windows Update"
                )
                return True
            else:
                self.logger.error(
                    f"Windows Update installation failed for {device_name}"
                )
                return False

        except Exception as e:
            self.logger.error(f"Error installing via Windows Update: {str(e)}")
            return False

    def _install_via_windows_update_interactive(self, update: Dict[str, Any]) -> bool:
        """Install via Windows Update with interactive feedback"""
        device_name = update.get("device_name", "Unknown")

        if self.verbose_mode:
            self.logger.info(f"🪟 Installing via Windows Update: {device_name}")

        try:
            # Use PowerShell to trigger Windows Update
            ps_script = f"""
            Get-WindowsUpdate -AcceptAll -Install -IgnoreReboot | Where-Object {{$_.Title -like "*{device_name}*"}}
            """

            cmd = ["powershell", "-Command", ps_script]

            if self.verbose_mode:
                self.logger.info(f"  Executing Windows Update search...")

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=600  # 10 minutes timeout
            )

            if result.returncode == 0:
                if self.verbose_mode:
                    self.logger.info(f"✅ Windows Update installation completed")
                return True
            else:
                if self.verbose_mode:
                    self.logger.info(f"ℹ️ No Windows Update available for this device")
                return False

        except Exception as e:
            if self.verbose_mode:
                self.logger.error(f"❌ Windows Update installation error: {str(e)}")
            return False

    def _backup_current_driver(self, update: Dict[str, Any]):
        """Create backup of current driver"""
        try:
            device_name = update.get("device_name", "Unknown")

            # Create device-specific backup directory
            device_backup_dir = os.path.join(
                self.backup_dir, self._sanitize_filename(device_name)
            )
            os.makedirs(device_backup_dir, exist_ok=True)

            # Export current driver using pnputil
            cmd = ["pnputil", "/export-driver", "*", device_backup_dir]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            if result.returncode == 0:
                self.logger.info(f"Created driver backup for {device_name}")
            else:
                self.logger.warning(f"Failed to create driver backup for {device_name}")

        except Exception as e:
            self.logger.warning(f"Error creating driver backup: {str(e)}")

    def _generate_driver_filename(self, update: Dict[str, Any]) -> str:
        """Generate appropriate filename for driver download"""
        device_name = update.get("device_name", "Unknown")
        manufacturer = update.get("manufacturer", "Unknown")
        version = update.get("new_version", "1.0.0.0")

        # Sanitize filename
        safe_device_name = self._sanitize_filename(device_name)
        safe_manufacturer = self._sanitize_filename(manufacturer)

        # Determine file extension based on manufacturer
        if "nvidia" in manufacturer.lower():
            ext = ".exe"
        elif "amd" in manufacturer.lower():
            ext = ".exe"
        elif "intel" in manufacturer.lower():
            ext = ".exe"
        else:
            ext = ".exe"

        return f"{safe_manufacturer}_{safe_device_name}_{version}{ext}"

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for Windows filesystem"""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "_")

        # Limit length
        if len(filename) > 50:
            filename = filename[:50]

        return filename.strip()

    def rollback_driver(self, device_name: str) -> bool:
        """Rollback driver to previous version"""
        try:
            self.logger.info(f"Rolling back driver for {device_name}")

            # Use pnputil to rollback driver
            cmd = ["pnputil", "/delete-driver", "/uninstall"]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            if result.returncode == 0:
                self.logger.info(f"Successfully rolled back driver for {device_name}")
                return True
            else:
                self.logger.error(f"Failed to rollback driver for {device_name}")
                return False

        except Exception as e:
            self.logger.error(f"Error rolling back driver: {str(e)}")
            return False

    def cleanup(self):
        """Clean up temporary files"""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                self.logger.info("Cleaned up temporary files")
        except Exception as e:
            self.logger.warning(f"Error cleaning up temporary files: {str(e)}")

    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()
