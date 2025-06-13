import json
import os
import sys
import threading
import tkinter as tk
from datetime import datetime
from tkinter import font as tkFont
from tkinter import messagebox, scrolledtext, ttk

from driver_installer import DriverInstaller
from driver_scanner import DriverScanner
from update_checker import UpdateChecker
from utils.logger import Logger
from utils.system_utils import SystemUtils

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class DriverUpdaterGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Windows Driver Updater - Enhanced v1.0.3")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        # Modern styling
        self.setup_styles()

        # Set icon and appearance
        self.root.configure(bg="#f0f0f0")

        # Initialize components
        self.logger = Logger()
        self.scanner = DriverScanner(self.logger)
        self.update_checker = UpdateChecker(self.logger)
        self.installer = DriverInstaller(self.logger)
        self.system_utils = SystemUtils(self.logger)

        # Variables
        self.drivers_data = []
        self.updates_available = []
        self.scanning = False
        self.checking_updates = False
        self.installing = False
        self.verbose_mode = tk.BooleanVar(value=True)
        self.auto_install = tk.BooleanVar(value=False)
        self.relaxed_validation = tk.BooleanVar(value=True)

        self.setup_ui()
        self.check_admin_privileges()

        # Add welcome message
        self.logger.info("Windows Driver Updater Enhanced v1.0.3 started")
        self.logger.info(
            "Enhanced features: Verbose output, Interactive installation, Relaxed validation"
        )

    def setup_styles(self):
        """Setup modern UI styles"""
        style = ttk.Style()
        style.theme_use("clam")

        # Configure custom styles
        style.configure(
            "Title.TLabel", font=("Segoe UI", 18, "bold"), foreground="#2c3e50"
        )
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10), foreground="#34495e")
        style.configure("Success.TLabel", foreground="#27ae60")
        style.configure("Warning.TLabel", foreground="#f39c12")
        style.configure("Error.TLabel", foreground="#e74c3c")

        # Button styles
        style.configure("Action.TButton", font=("Segoe UI", 9, "bold"))
        style.map(
            "Action.TButton", background=[("active", "#3498db"), ("pressed", "#2980b9")]
        )

    def setup_ui(self):
        """Setup the enhanced user interface"""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        # Header section
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        header_frame.columnconfigure(0, weight=1)

        # Title with icon
        title_label = ttk.Label(
            header_frame,
            text="🔧 Windows Driver Updater - Enhanced",
            style="Title.TLabel",
        )
        title_label.grid(row=0, column=0, sticky=tk.W)

        subtitle_label = ttk.Label(
            header_frame,
            text="Advanced driver management with verbose output and interactive installation",
            style="Subtitle.TLabel",
        )
        subtitle_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))

        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))

        ttk.Checkbutton(
            options_frame,
            text="Verbose output (recommended)",
            variable=self.verbose_mode,
        ).grid(row=0, column=0, sticky=tk.W, padx=(0, 20))

        ttk.Checkbutton(
            options_frame, text="Auto-install all updates", variable=self.auto_install
        ).grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        ttk.Checkbutton(
            options_frame, text="Relaxed validation", variable=self.relaxed_validation
        ).grid(row=0, column=2, sticky=tk.W)

        # Enhanced buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 15))

        # Left side buttons
        left_buttons = ttk.Frame(buttons_frame)
        left_buttons.pack(side=tk.LEFT)

        self.scan_btn = ttk.Button(
            left_buttons,
            text="🔍 Scan Drivers",
            command=self.start_scan,
            style="Action.TButton",
        )
        self.scan_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.check_updates_btn = ttk.Button(
            left_buttons,
            text="🌐 Check Updates",
            command=self.start_update_check,
            state=tk.DISABLED,
            style="Action.TButton",
        )
        self.check_updates_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.install_btn = ttk.Button(
            left_buttons,
            text="⚡ Install Updates",
            command=self.start_installation,
            state=tk.DISABLED,
            style="Action.TButton",
        )
        self.install_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Right side buttons
        right_buttons = ttk.Frame(buttons_frame)
        right_buttons.pack(side=tk.RIGHT)

        self.restore_btn = ttk.Button(
            right_buttons,
            text="💾 Create Restore Point",
            command=self.create_restore_point,
        )
        # Enhanced Notebook for tabs
        self.restore_btn.pack(side=tk.LEFT, padx=(10, 0))
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Drivers tab with enhanced display
        self.drivers_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.drivers_frame, text="🖥️ Drivers")
        self.setup_drivers_tab()

        # Updates tab with progress tracking
        self.updates_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.updates_frame, text="🔄 Updates")
        self.setup_updates_tab()

        # Enhanced log tab with filtering
        self.log_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.log_frame, text="📋 Verbose Log")
        self.setup_log_tab()

        # System info tab
        self.system_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.system_frame, text="💻 System Info")
        self.setup_system_tab()

        # Enhanced status bar with icons
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(15, 0))
        status_frame.columnconfigure(1, weight=1)

        self.status_var = tk.StringVar()
        self.status_var.set("🟢 Ready - Select an operation to begin")

        status_icon = ttk.Label(status_frame, text="ℹ️")
        status_icon.grid(row=0, column=0, padx=(0, 5))

        status_bar = ttk.Label(
            status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        status_bar.grid(row=0, column=1, sticky=(tk.W, tk.E))

        # Enhanced progress bar with label
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        progress_frame.columnconfigure(0, weight=1)

        self.progress = ttk.Progressbar(progress_frame, mode="indeterminate")
        self.progress.grid(row=0, column=0, sticky=(tk.W, tk.E))

        self.progress_label = ttk.Label(progress_frame, text="")
        self.progress_label.grid(row=1, column=0, pady=(2, 0))
        self.notebook.add(self.drivers_frame, text="Drivers")
        self.setup_drivers_tab()

        # Updates tab
        self.updates_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.updates_frame, text="Updates")
        self.setup_updates_tab()

        # Log tab
        self.log_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.log_frame, text="Log")
        self.setup_log_tab()

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(
            main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        status_bar.grid(
            row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0)
        )

        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode="indeterminate")
        self.progress.grid(
            row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0)
        )

    def setup_drivers_tab(self):
        """Setup the enhanced drivers list tab"""
        # Top frame for filters and stats
        top_frame = ttk.Frame(self.drivers_frame)
        top_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        # Stats labels
        self.driver_stats = ttk.Label(top_frame, text="No drivers scanned yet")
        self.driver_stats.pack(side=tk.LEFT)

        # Filter frame
        filter_frame = ttk.Frame(top_frame)
        filter_frame.pack(side=tk.RIGHT)

        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=(0, 5))
        self.driver_filter = ttk.Combobox(
            filter_frame,
            values=[
                "All",
                "Graphics",
                "Audio",
                "Network",
                "Storage",
                "System",
            ],
        )
        self.driver_filter.set("All")
        self.driver_filter.pack(side=tk.LEFT)
        self.driver_filter.bind("<<ComboboxSelected>>", self.filter_drivers)

        # Enhanced Treeview for drivers with more columns
        columns = (
            "Device",
            "Driver",
            "Version",
            "Date",
            "Status",
            "Manufacturer",
            "Type",
        )
        self.drivers_tree = ttk.Treeview(
            self.drivers_frame, columns=columns, show="headings", height=15
        )

        # Configure columns with better sizing
        column_widths = {
            "Device": 200,
            "Driver": 150,
            "Version": 100,
            "Date": 100,
            "Status": 80,
            "Manufacturer": 120,
            "Type": 100,
        }

        for col in columns:
            self.drivers_tree.heading(col, text=col)
            self.drivers_tree.column(col, width=column_widths.get(col, 100))

        # Scrollbars
        drivers_v_scrollbar = ttk.Scrollbar(
            self.drivers_frame, orient=tk.VERTICAL, command=self.drivers_tree.yview
        )
        drivers_h_scrollbar = ttk.Scrollbar(
            self.drivers_frame, orient=tk.HORIZONTAL, command=self.drivers_tree.xview
        )

        self.drivers_tree.configure(
            yscrollcommand=drivers_v_scrollbar.set,
            xscrollcommand=drivers_h_scrollbar.set,
        )

        # Pack widgets with proper scrollbars
        tree_frame = ttk.Frame(self.drivers_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))

        self.drivers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        drivers_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        drivers_h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_updates_tab(self):
        """Setup the enhanced updates available tab"""
        # Top frame for update stats and options
        top_frame = ttk.Frame(self.updates_frame)
        top_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        self.update_stats = ttk.Label(top_frame, text="No updates checked yet")
        self.update_stats.pack(side=tk.LEFT)

        # Update options
        options_frame = ttk.Frame(top_frame)
        options_frame.pack(side=tk.RIGHT)

        ttk.Button(
            options_frame, text="Select All", command=self.select_all_updates
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(
            options_frame, text="Select None", command=self.select_no_updates
        ).pack(side=tk.LEFT)

        # Enhanced Treeview for updates with checkboxes
        columns = (
            "Select",
            "Device",
            "Current Version",
            "New Version",
            "Size",
            "Priority",
            "Status",
        )
        self.updates_tree = ttk.Treeview(
            self.updates_frame, columns=columns, show="headings", height=15
        )

        # Configure columns
        column_widths = {
            "Select": 60,
            "Device": 200,
            "Current Version": 120,
            "New Version": 120,
            "Size": 80,
            "Priority": 80,
            "Status": 100,
        }

        for col in columns:
            self.updates_tree.heading(col, text=col)
            self.updates_tree.column(col, width=column_widths.get(col, 100))

        # Bind click event for checkbox simulation
        self.updates_tree.bind("<Button-1>", self.on_update_item_click)

        # Scrollbars for updates
        updates_v_scrollbar = ttk.Scrollbar(
            self.updates_frame, orient=tk.VERTICAL, command=self.updates_tree.yview
        )
        updates_h_scrollbar = ttk.Scrollbar(
            self.updates_frame, orient=tk.HORIZONTAL, command=self.updates_tree.xview
        )

        self.updates_tree.configure(
            yscrollcommand=updates_v_scrollbar.set,
            xscrollcommand=updates_h_scrollbar.set,
        )

        # Pack updates widgets
        updates_tree_frame = ttk.Frame(self.updates_frame)
        updates_tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))

        self.updates_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        updates_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        updates_h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_log_tab(self):
        """Setup the enhanced log display tab with filtering"""
        # Log controls frame
        log_controls = ttk.Frame(self.log_frame)
        log_controls.pack(fill=tk.X, padx=10, pady=(10, 5))

        # Log level filter
        ttk.Label(log_controls, text="Log Level:").pack(side=tk.LEFT, padx=(0, 5))
        self.log_level_filter = ttk.Combobox(
            log_controls, values=["All", "INFO", "WARNING", "ERROR"]
        )
        self.log_level_filter.set("All")
        self.log_level_filter.pack(side=tk.LEFT, padx=(0, 10))

        # Clear log button
        ttk.Button(log_controls, text="Clear Log", command=self.clear_log).pack(
            side=tk.LEFT, padx=(0, 10)
        )

        # Save log button
        ttk.Button(log_controls, text="Save Log", command=self.save_log).pack(
            side=tk.LEFT
        )

        # Auto-scroll checkbox
        self.auto_scroll = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            log_controls, text="Auto-scroll", variable=self.auto_scroll
        ).pack(side=tk.RIGHT)

        # Enhanced log text with syntax highlighting
        log_text_frame = ttk.Frame(self.log_frame)
        log_text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))

        self.log_text = scrolledtext.ScrolledText(
            log_text_frame,
            width=100,
            height=25,
            font=("Consolas", 9),
            wrap=tk.WORD,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Configure text tags for color coding
        self.log_text.tag_configure("INFO", foreground="#2ecc71")
        self.log_text.tag_configure("WARNING", foreground="#f39c12")
        self.log_text.tag_configure("ERROR", foreground="#e74c3c")
        self.log_text.tag_configure("DEBUG", foreground="#9b59b6")

        # Add log handler to display logs in GUI
        self.logger.add_gui_handler(self.log_text, self.auto_scroll)

    def setup_system_tab(self):
        """Setup system information tab"""
        # System info display
        info_frame = ttk.LabelFrame(
            self.system_frame, text="System Information", padding="10"
        )
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.system_info_text = scrolledtext.ScrolledText(
            info_frame,
            width=80,
            height=20,
            font=("Consolas", 9),
            state=tk.DISABLED,
        )
        self.system_info_text.pack(fill=tk.BOTH, expand=True)

        # Load system info
        self.load_system_info()

    def filter_drivers(self, event=None):
        """Filter drivers by category"""
        filter_value = self.driver_filter.get()
        # Implementation for filtering drivers by category
        # This will be enhanced based on driver categories
        pass

    def select_all_updates(self):
        """Select all updates for installation"""
        for item in self.updates_tree.get_children():
            self.updates_tree.set(item, "Select", "☑️")

    def select_no_updates(self):
        """Deselect all updates"""
        for item in self.updates_tree.get_children():
            self.updates_tree.set(item, "Select", "☐")

    def on_update_item_click(self, event):
        """Handle click on update item for checkbox toggle"""
        item = self.updates_tree.identify("item", event.x, event.y)
        column = self.updates_tree.identify("column", event.x, event.y)

        if item and column == "#1":  # Select column
            current_value = self.updates_tree.set(item, "Select")
            new_value = "☑️" if current_value == "☐" else "☐"
            self.updates_tree.set(item, "Select", new_value)

    def clear_log(self):
        """Clear the log display"""
        self.log_text.delete(1.0, tk.END)

    def save_log(self):
        """Save log to file"""
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[
                ("Log files", "*.log"),
                ("Text files", "*.txt"),
                ("All files", "*"),
            ],
        )
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(self.log_text.get(1.0, tk.END))
                messagebox.showinfo("Success", f"Log saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save log: {str(e)}")

    def load_system_info(self):
        """Load and display system information"""
        try:
            import platform

            import psutil

            info_text = []
            info_text.append(f"System: {platform.system()} {platform.release()}")
            info_text.append(f"Version: {platform.version()}")
            info_text.append(f"Architecture: {platform.architecture()[0]}")
            info_text.append(f"Processor: {platform.processor()}")
            info_text.append(f"CPU Cores: {psutil.cpu_count()}")
            info_text.append(f"Memory: {psutil.virtual_memory().total // (1024**3)} GB")
            info_text.append(f"Python Version: {platform.python_version()}")
            info_text.append("")
            info_text.append("Driver Updater Configuration:")
            info_text.append(f"Verbose Mode: {self.verbose_mode.get()}")
            info_text.append(f"Auto Install: {self.auto_install.get()}")
            info_text.append(f"Relaxed Validation: {self.relaxed_validation.get()}")

            self.system_info_text.config(state=tk.NORMAL)
            self.system_info_text.delete(1.0, tk.END)
            self.system_info_text.insert(1.0, "\n".join(info_text))
            self.system_info_text.config(state=tk.DISABLED)

        except Exception as e:
            self.logger.error(f"Failed to load system info: {str(e)}")

    def check_admin_privileges(self):
        """Enhanced admin privilege check"""
        if not self.system_utils.is_admin():
            # More informative admin warning
            result = messagebox.askquestion(
                "Administrator Privileges Required",
                "🔒 Administrator privileges are required for driver installation.\n\n"
                "Without admin rights, you can:\n"
                "✓ Scan for drivers\n"
                "✓ Check for updates\n"
                "✗ Install driver updates\n\n"
                "Would you like to continue anyway?\n"
                "(You can restart as administrator later)",
                icon="warning",
            )
            if result == "no":
                self.root.quit()
            else:
                self.logger.warning(
                    "Running without administrator privileges - installation features disabled"
                )
                self.install_btn.config(state=tk.DISABLED)
                self.restore_btn.config(state=tk.DISABLED)

    def start_scan(self):
        """Enhanced driver scanning with verbose output"""
        if self.scanning:
            return

        self.scanning = True
        self.scan_btn.config(state=tk.DISABLED)
        self.check_updates_btn.config(state=tk.DISABLED)

        # Enhanced status messages
        self.status_var.set("🔍 Scanning system drivers...")
        self.progress_label.config(text="Initializing driver scan...")
        self.progress.start()

        # Clear previous data
        for item in self.drivers_tree.get_children():
            self.drivers_tree.delete(item)
        self.drivers_data = []

        if self.verbose_mode.get():
            self.logger.info("=" * 60)
            self.logger.info("STARTING ENHANCED DRIVER SCAN")
            self.logger.info("=" * 60)
            self.logger.info(f"Scan options:")
            self.logger.info(f"  - Verbose mode: {self.verbose_mode.get()}")
            self.logger.info(f"  - Relaxed validation: {self.relaxed_validation.get()}")

        # Start scanning thread
        scan_thread = threading.Thread(target=self.scan_drivers_thread)
        scan_thread.daemon = True
        scan_thread.start()

    def scan_drivers_thread(self):
        """Enhanced driver scanning thread with progress updates"""
        try:
            if self.verbose_mode.get():
                self.logger.info("Initializing WMI connection...")

            # Update progress
            self.root.after(
                0,
                lambda: self.progress_label.config(
                    text="Connecting to Windows Management Interface..."
                ),
            )

            self.drivers_data = self.scanner.scan_all_drivers()

            if self.verbose_mode.get():
                self.logger.info(f"Scan completed successfully!")
                self.logger.info(f"Found {len(self.drivers_data)} drivers total")

                # Log driver categories
                categories = self.scanner.get_driver_categories(self.drivers_data)
                for category, drivers in categories.items():
                    if drivers:
                        self.logger.info(f"  - {category}: {len(drivers)} drivers")

            self.root.after(0, self.on_scan_complete)
        except Exception as e:
            self.logger.error(f"Enhanced scan error: {str(e)}")
            if self.verbose_mode.get():
                import traceback

                self.logger.error(f"Detailed error: {traceback.format_exc()}")
            self.root.after(0, self.on_scan_error, str(e))

    def on_scan_complete(self):
        """Enhanced scan completion handler"""
        self.progress.stop()
        self.progress_label.config(text="")
        self.scanning = False
        self.scan_btn.config(state=tk.NORMAL)
        self.check_updates_btn.config(state=tk.NORMAL)

        # Enhanced driver display with categories and colors
        for driver in self.drivers_data:
            item = self.drivers_tree.insert(
                "",
                tk.END,
                values=(
                    driver.get("device_name", "Unknown"),
                    driver.get("driver_name", "Unknown"),
                    driver.get("version", "Unknown"),
                    driver.get("date", "Unknown"),
                    driver.get("status", "Unknown"),
                    driver.get("manufacturer", "Unknown"),
                    driver.get("driver_type", "Unknown"),
                ),
            )

            # Color code by status
            status = driver.get("status", "").lower()
            if "error" in status or "problem" in status:
                self.drivers_tree.set(
                    item, "Status", "⚠️ " + driver.get("status", "Unknown")
                )
            elif "ok" in status or "working" in status:
                self.drivers_tree.set(
                    item, "Status", "✅ " + driver.get("status", "Unknown")
                )

        # Update stats
        self.driver_stats.config(text=f"Found {len(self.drivers_data)} drivers")
        self.status_var.set(f"🟢 Scan complete - Found {len(self.drivers_data)} drivers")

        if self.verbose_mode.get():
            self.logger.info("=" * 60)
            self.logger.info("DRIVER SCAN SUMMARY")
            self.logger.info("=" * 60)

    def on_scan_error(self, error_msg):
        """Enhanced scan error handler"""
        self.progress.stop()
        self.progress_label.config(text="")
        self.scanning = False
        self.scan_btn.config(state=tk.NORMAL)
        self.status_var.set("🔴 Scan failed")

        error_dialog = messagebox.showerror(
            "Enhanced Scan Error",
            f"Failed to scan drivers:\n\n{error_msg}\n\n"
            "Check the Verbose Log tab for detailed information.",
        )

    def start_update_check(self):
        """Enhanced update checking with verbose progress"""
        if self.checking_updates or not self.drivers_data:
            return

        self.checking_updates = True
        self.check_updates_btn.config(state=tk.DISABLED)
        self.install_btn.config(state=tk.DISABLED)

        self.status_var.set("🌐 Checking for driver updates...")
        self.progress_label.config(text="Initializing update check...")
        self.progress.start()

        # Clear previous updates
        for item in self.updates_tree.get_children():
            self.updates_tree.delete(item)
        self.updates_available = []

        if self.verbose_mode.get():
            self.logger.info("=" * 60)
            self.logger.info("STARTING ENHANCED UPDATE CHECK")
            self.logger.info("=" * 60)
            self.logger.info(
                f"Checking {len(self.drivers_data)} drivers for updates..."
            )
            self.logger.info(f"Relaxed validation: {self.relaxed_validation.get()}")

        # Start update check thread
        update_thread = threading.Thread(target=self.check_updates_thread)
        update_thread.daemon = True
        update_thread.start()

    def check_updates_thread(self):
        """Enhanced update checking thread with detailed progress"""
        try:
            if self.verbose_mode.get():
                self.logger.info("Contacting manufacturer websites...")

            # Enhanced update checker with relaxed validation
            self.update_checker.set_relaxed_validation(self.relaxed_validation.get())
            self.update_checker.set_verbose_mode(self.verbose_mode.get())

            self.updates_available = self.update_checker.check_for_updates(
                self.drivers_data, progress_callback=self.update_progress_callback
            )

            if self.verbose_mode.get():
                self.logger.info(f"Update check completed!")
                self.logger.info(
                    f"Found {len(self.updates_available)} available updates"
                )
                for update in self.updates_available:
                    self.logger.info(
                        f"  - {update.get('device_name')}: {update.get('current_version')} → {update.get('new_version')}"
                    )

            self.root.after(0, self.on_update_check_complete)
        except Exception as e:
            self.logger.error(f"Enhanced update check error: {str(e)}")
            if self.verbose_mode.get():
                import traceback

                self.logger.error(f"Detailed error: {traceback.format_exc()}")
            self.root.after(0, self.on_update_check_error, str(e))

    def update_progress_callback(self, current, total, device_name):
        """Callback for update check progress"""
        if self.verbose_mode.get():
            self.logger.info(f"Checking {current}/{total}: {device_name}")
        self.root.after(
            0,
            lambda: self.progress_label.config(
                text=f"Checking updates {current}/{total}: {device_name[:30]}..."
            ),
        )

    def on_update_check_complete(self):
        """Enhanced update check completion"""
        self.progress.stop()
        self.progress_label.config(text="")
        self.checking_updates = False
        self.check_updates_btn.config(state=tk.NORMAL)

        # Enhanced updates display with priority and selection
        for update in self.updates_available:
            priority = self.calculate_update_priority(update)
            item = self.updates_tree.insert(
                "",
                tk.END,
                values=(
                    "☐",  # Selection checkbox
                    update.get("device_name", "Unknown"),
                    update.get("current_version", "Unknown"),
                    update.get("new_version", "Unknown"),
                    update.get("download_size", "Unknown"),
                    priority,
                    "🟢 Available",
                ),
            )

            # Auto-select high priority updates
            if priority == "High":
                self.updates_tree.set(item, "Select", "☑️")

        if self.updates_available and self.system_utils.is_admin():
            self.install_btn.config(state=tk.NORMAL)

        # Update stats
        self.update_stats.config(
            text=f"Found {len(self.updates_available)} available updates"
        )
        self.status_var.set(
            f"🟢 Update check complete - {len(self.updates_available)} updates available"
        )

        if self.verbose_mode.get():
            self.logger.info("=" * 60)
            self.logger.info("UPDATE CHECK SUMMARY")
            self.logger.info("=" * 60)

    def calculate_update_priority(self, update):
        """Calculate update priority based on device type and version difference"""
        device_name = update.get("device_name", "").lower()

        # High priority for graphics, security, and critical drivers
        if any(
            keyword in device_name
            for keyword in ["graphics", "display", "security", "chipset"]
        ):
            return "High"
        # Medium priority for audio and network
        elif any(
            keyword in device_name
            for keyword in ["audio", "network", "ethernet", "wifi"]
        ):
            return "Medium"
        else:
            return "Low"

    def on_update_check_error(self, error_msg):
        """Enhanced update check error handler"""
        self.progress.stop()
        self.progress_label.config(text="")
        self.checking_updates = False
        self.check_updates_btn.config(state=tk.NORMAL)
        self.status_var.set("🔴 Update check failed")

        messagebox.showerror(
            "Enhanced Update Check Error",
            f"Failed to check for updates:\n\n{error_msg}\n\n"
            "This may be due to network connectivity or manufacturer website changes.\n"
            "Check the Verbose Log tab for detailed information.",
        )

    def start_installation(self):
        """Enhanced interactive installation process"""
        if not self.updates_available or self.installing:
            return

        # Get selected updates
        selected_updates = []
        for item in self.updates_tree.get_children():
            if self.updates_tree.set(item, "Select") == "☑️":
                device_name = self.updates_tree.set(item, "Device")
                for update in self.updates_available:
                    if update.get("device_name") == device_name:
                        selected_updates.append(update)
                        break

        if not selected_updates:
            messagebox.showwarning(
                "No Updates Selected", "Please select at least one update to install."
            )
            return

        # Enhanced confirmation dialog
        if not self.auto_install.get():
            result = self.show_installation_confirmation(selected_updates)
            if result != "yes":
                return

        self.installing = True
        self.install_btn.config(state=tk.DISABLED)
        self.status_var.set("⚡ Installing driver updates...")
        self.progress_label.config(text="Preparing installation...")
        self.progress.start()

        if self.verbose_mode.get():
            self.logger.info("=" * 60)
            self.logger.info("STARTING ENHANCED INSTALLATION")
            self.logger.info("=" * 60)
            self.logger.info(f"Installing {len(selected_updates)} selected updates")
            self.logger.info(f"Interactive mode: {not self.auto_install.get()}")

        # Start installation thread
        install_thread = threading.Thread(
            target=self.install_updates_thread, args=(selected_updates,)
        )
        install_thread.daemon = True
        install_thread.start()

    def show_installation_confirmation(self, selected_updates):
        """Show detailed installation confirmation dialog"""
        # Create custom dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Confirm Driver Installation")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        dialog.geometry(
            "+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50)
        )

        # Header
        header = ttk.Label(
            dialog,
            text="⚡ Driver Installation Confirmation",
            font=("Segoe UI", 14, "bold"),
        )
        header.pack(pady=10)

        # Info frame
        info_frame = ttk.LabelFrame(dialog, text="Installation Details", padding="10")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Details text
        details_text = scrolledtext.ScrolledText(info_frame, height=10, width=70)
        details_text.pack(fill=tk.BOTH, expand=True)

        details_content = []
        details_content.append("The following driver updates will be installed:\n")
        for i, update in enumerate(selected_updates, 1):
            details_content.append(f"{i}. {update.get('device_name', 'Unknown')}")
            details_content.append(
                f"   Current: {update.get('current_version', 'Unknown')}"
            )
            details_content.append(f"   New: {update.get('new_version', 'Unknown')}")
            details_content.append(f"   Size: {update.get('download_size', 'Unknown')}")
            details_content.append("")

        details_content.append("SAFETY MEASURES:")
        details_content.append("✓ System restore point will be created automatically")
        details_content.append("✓ Current drivers will be backed up")
        details_content.append("✓ Digital signature verification (if enabled)")
        details_content.append("✓ Rollback available if installation fails")

        details_text.insert(1.0, "\n".join(details_content))
        details_text.config(state=tk.DISABLED)

        # Button frame
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        result = [None]  # Use list to allow modification in nested function

        def on_yes():
            result[0] = "yes"
            dialog.destroy()

        def on_no():
            result[0] = "no"
            dialog.destroy()

        ttk.Button(
            button_frame,
            text="✅ Install Updates",
            command=on_yes,
            style="Action.TButton",
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="❌ Cancel", command=on_no).pack(side=tk.LEFT)

        # Wait for dialog to close
        dialog.wait_window()
        return result[0]

    def install_updates_thread(self, selected_updates):
        """Enhanced installation thread with interactive prompts"""
        try:
            success_count = 0
            self.installer.set_verbose_mode(self.verbose_mode.get())
            self.installer.set_interactive_mode(not self.auto_install.get())

            for i, update in enumerate(selected_updates):
                if self.verbose_mode.get():
                    self.logger.info(
                        f"Installing update {i+1}/{len(selected_updates)}: {update.get('device_name')}"
                    )

                self.root.after(
                    0,
                    lambda i=i, total=len(selected_updates), name=update.get(
                        "device_name"
                    ): self.progress_label.config(
                        text=f"Installing {i+1}/{total}: {name[:30]}"
                    ),
                )

                if self.installer.install_single_update_interactive(update):
                    success_count += 1
                    if self.verbose_mode.get():
                        self.logger.info(
                            f"✅ Successfully installed: {update.get('device_name')}"
                        )
                else:
                    if self.verbose_mode.get():
                        self.logger.error(
                            f"❌ Failed to install: {update.get('device_name')}"
                        )

            self.root.after(
                0, self.on_installation_complete, success_count, len(selected_updates)
            )

        except Exception as e:
            self.logger.error(f"Enhanced installation error: {str(e)}")
            if self.verbose_mode.get():
                import traceback

                self.logger.error(f"Detailed error: {traceback.format_exc()}")
            self.root.after(0, self.on_installation_error, str(e))

    def on_installation_complete(self, success_count, total_count):
        """Enhanced installation completion handler"""
        self.progress.stop()
        self.progress_label.config(text="")
        self.installing = False
        self.install_btn.config(state=tk.NORMAL)

        # Enhanced completion message
        if success_count == total_count:
            icon = "🎉"
            title = "Installation Successful!"
            message = f"All {total_count} driver updates were installed successfully!"
        elif success_count > 0:
            icon = "⚠️"
            title = "Partial Installation"
            message = f"{success_count} out of {total_count} updates were installed successfully."
        else:
            icon = "❌"
            title = "Installation Failed"
            message = "No updates were installed successfully."

        message += "\n\nPlease restart your computer to complete the installation."

        if self.verbose_mode.get():
            self.logger.info("=" * 60)
            self.logger.info("INSTALLATION SUMMARY")
            self.logger.info("=" * 60)
            self.logger.info(f"Total updates: {total_count}")
            self.logger.info(f"Successful: {success_count}")
            self.logger.info(f"Failed: {total_count - success_count}")

        messagebox.showinfo(title, f"{icon} {message}")
        self.status_var.set(
            f"🟢 Installation complete - {success_count}/{total_count} successful"
        )

    def on_installation_error(self, error_msg):
        """Enhanced installation error handler"""
        self.progress.stop()
        self.progress_label.config(text="")
        self.installing = False
        self.install_btn.config(state=tk.NORMAL)
        self.status_var.set("🔴 Installation failed")

        messagebox.showerror(
            "Enhanced Installation Error",
            f"Installation process failed:\n\n{error_msg}\n\n"
            "Check the Verbose Log tab for detailed information.\n"
            "Your system should be automatically restored to the previous state.",
        )

    def create_restore_point(self):
        """Enhanced restore point creation"""
        if self.verbose_mode.get():
            self.logger.info("Creating system restore point...")

        self.status_var.set("💾 Creating system restore point...")

        try:
            success = self.system_utils.create_restore_point(
                "Driver Updater - Manual Restore Point"
            )
            if success:
                if self.verbose_mode.get():
                    self.logger.info("✅ System restore point created successfully")
                messagebox.showinfo(
                    "Success", "💾 System restore point created successfully!"
                )
                self.status_var.set("🟢 Restore point created")
            else:
                if self.verbose_mode.get():
                    self.logger.error("❌ Failed to create system restore point")
                messagebox.showerror(
                    "Error",
                    "❌ Failed to create system restore point.\nCheck the log for details.",
                )
                self.status_var.set("🔴 Restore point failed")
        except Exception as e:
            self.logger.error(f"Error creating restore point: {str(e)}")
            messagebox.showerror("Error", f"❌ Error creating restore point:\n{str(e)}")
            self.status_var.set("🔴 Restore point error")

    def run(self):
        """Start the enhanced GUI application"""
        try:
            self.logger.info("Starting Windows Driver Updater Enhanced GUI")
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Application error: {str(e)}")
            raise


def main():
    """Main entry point for the enhanced application"""
    try:
        app = DriverUpdaterGUI()
        app.run()
    except Exception as e:
        messagebox.showerror(
            "Application Error", f"Failed to start enhanced application:\n{str(e)}"
        )
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
