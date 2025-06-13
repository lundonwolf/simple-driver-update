# Windows Driver Updater - Usage Guide

## Quick Start

### Method 1: Simple Batch File
1. Double-click `run.bat`
2. Follow the prompts
3. The application will install dependencies if needed

### Method 2: PowerShell Script
1. Right-click on `run.ps1` and select "Run with PowerShell"
2. Or open PowerShell as Administrator and run: `.\run.ps1 -RunAsAdmin`

### Method 3: Direct Python
1. Install dependencies: `python setup.py`
2. Run application: `python main.py`

## Features

### 1. Driver Scanning
- Click "Scan Drivers" to scan all installed drivers
- View results in the "Drivers" tab
- Shows device name, driver version, date, and status

### 2. Update Checking
- Click "Check for Updates" after scanning
- View available updates in the "Updates" tab
- Shows current vs. new version and download size

### 3. Driver Installation
- Click "Install Updates" to install all available updates
- Automatic system restore point creation
- Progress tracking and logging

### 4. Safety Features
- System restore point creation before installation
- Driver backup before updates
- Administrator privilege checking
- Digital signature verification

## GUI Interface

### Main Window
- **Scan Drivers**: Scans your system for all installed drivers
- **Check for Updates**: Checks manufacturer websites for newer versions
- **Install Updates**: Downloads and installs available updates
- **Create Restore Point**: Manually creates a system restore point

### Tabs
1. **Drivers**: List of all scanned drivers with details
2. **Updates**: List of available driver updates
3. **Log**: Real-time application log with status messages

### Status Bar
- Shows current operation status
- Progress bar for long-running operations

## Supported Manufacturers

The application can check for updates from:
- **NVIDIA** - Graphics drivers
- **AMD** - Graphics and chipset drivers
- **Intel** - Graphics, chipset, and network drivers
- **Realtek** - Audio and network drivers
- **Microsoft** - Windows Update drivers
- **Generic** - Basic update detection for other manufacturers

## Configuration

Edit `config/settings.json` to customize:
- Update check intervals
- Timeout settings
- Safety features
- UI preferences
- Manufacturer URLs

## Logs

Log files are stored in:
- `logs/` directory (relative to application)
- `%LOCALAPPDATA%\DriverUpdater\Logs\` (user data)

## Troubleshooting

### Common Issues

**"Not running as administrator"**
- Right-click the batch file and select "Run as administrator"
- Or use PowerShell with `-RunAsAdmin` parameter

**"Failed to install dependencies"**
- Run `python setup.py` manually
- Check internet connection
- Ensure Python is properly installed

**"WMI connection failed"**
- Run as administrator
- Check Windows Management Instrumentation service
- Restart the computer if necessary

**"Driver installation failed"**
- Ensure you have administrator privileges
- Check if antivirus is blocking the installation
- Verify driver signature and compatibility

### Debug Mode
Run with verbose logging:
```batch
python main.py --verbose
```

### Clean Installation
1. Run `python uninstall.py` to remove all data
2. Run `python setup.py` to reinstall
3. Run the application normally

## Safety Recommendations

1. **Always run as administrator** for full functionality
2. **Create a manual restore point** before major updates
3. **Check system stability** after driver updates
4. **Keep backups** of important data
5. **Test critical functions** after driver updates

## Command Line Options

```bash
python main.py [options]

Options:
  --verbose     Enable verbose logging
  --scan-only   Scan drivers but don't check for updates
  --no-gui      Run in command-line mode (future feature)
  --config      Specify custom configuration file
```

## File Structure

```
DriverUpdater/
├── main.py                 # Main application
├── driver_scanner.py       # System driver scanning
├── update_checker.py       # Online update detection
├── driver_installer.py     # Driver installation
├── setup.py               # Installation script
├── test.py                # Testing script
├── build.py               # Build executable script
├── uninstall.py           # Uninstaller
├── run.bat                # Windows batch launcher
├── run.ps1                # PowerShell launcher
├── requirements.txt       # Python dependencies
├── README.md              # Documentation
├── config/
│   └── settings.json      # Configuration file
├── utils/
│   ├── logger.py          # Logging utilities
│   └── system_utils.py    # System utilities
└── logs/                  # Log files
```

## Legal Notice

- This software modifies system drivers
- Always create backups before use
- Use at your own risk
- The authors are not responsible for system damage
- Ensure you have proper licenses for all drivers

## Support

For issues or questions:
1. Check the log files for error details
2. Run the test script: `python test.py`
3. Review this usage guide
4. Check the README.md for technical details
