import logging
import os
import tkinter as tk
from datetime import datetime


class Logger:
    """Enhanced logging utility for the Driver Updater"""

    def __init__(self, log_level=logging.INFO):
        self.logger = logging.getLogger("DriverUpdater")
        self.logger.setLevel(log_level)

        # Clear any existing handlers
        self.logger.handlers.clear()

        # Create logs directory
        self.log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
        )
        os.makedirs(self.log_dir, exist_ok=True)

        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"driver_updater_{timestamp}.log"
        self.log_file_path = os.path.join(self.log_dir, log_filename)

        # Create formatters
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_formatter = logging.Formatter("%(levelname)s: %(message)s")

        # File handler
        file_handler = logging.FileHandler(self.log_file_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # GUI handler placeholder
        self.gui_text_widget = None

        self.info("Logger initialized")

    def add_gui_handler(self, text_widget, auto_scroll_var=None):
        """Add GUI text widget for log display with enhanced formatting"""
        self.gui_text_widget = text_widget
        self.auto_scroll_var = auto_scroll_var

        # Configure text widget for better appearance
        if hasattr(text_widget, "tag_configure"):
            text_widget.tag_configure(
                "INFO", foreground="#2ecc71", font=("Consolas", 9)
            )
            text_widget.tag_configure(
                "WARNING", foreground="#f39c12", font=("Consolas", 9, "bold")
            )
            text_widget.tag_configure(
                "ERROR", foreground="#e74c3c", font=("Consolas", 9, "bold")
            )
            text_widget.tag_configure(
                "DEBUG", foreground="#9b59b6", font=("Consolas", 9)
            )
            text_widget.tag_configure(
                "SUCCESS", foreground="#27ae60", font=("Consolas", 9, "bold")
            )
            text_widget.tag_configure(
                "TIMESTAMP", foreground="#7f8c8d", font=("Consolas", 8)
            )

        self.info("Enhanced GUI log handler added")

    def _write_to_gui(self, level, message):
        """Write formatted message to GUI with color coding"""
        if self.gui_text_widget:
            try:
                timestamp = datetime.now().strftime("%H:%M:%S")

                # Insert timestamp
                self.gui_text_widget.insert(tk.END, f"[{timestamp}] ", "TIMESTAMP")

                # Insert level indicator with emoji
                level_indicators = {
                    "INFO": "ℹ️ INFO",
                    "WARNING": "⚠️ WARN",
                    "ERROR": "❌ ERROR",
                    "DEBUG": "🔍 DEBUG",
                    "SUCCESS": "✅ SUCCESS",
                }

                level_text = level_indicators.get(level, level)
                self.gui_text_widget.insert(tk.END, f"{level_text}: ", level)

                # Insert message
                self.gui_text_widget.insert(tk.END, f"{message}\n")

                # Auto-scroll if enabled
                if self.auto_scroll_var and self.auto_scroll_var.get():
                    self.gui_text_widget.see(
                        tk.END
                    )  # Limit text widget size (keep last 1000 lines)
                lines = self.gui_text_widget.get("1.0", tk.END).split("\n")
                if len(lines) > 1000:
                    # Remove first 100 lines
                    self.gui_text_widget.delete("1.0", f"{100}.0")

            except Exception as e:
                # Fallback to basic logging if GUI update fails
                pass

    def debug(self, message):
        """Log debug message"""
        self.logger.debug(message)

    def info(self, message):
        """Log info message"""
        self.logger.info(message)
        self._write_to_gui("INFO", message)

    def warning(self, message):
        """Log warning message"""
        self.logger.warning(message)
        self._write_to_gui("WARNING", message)

    def error(self, message):
        """Log error message"""
        self.logger.error(message)
        self._write_to_gui("ERROR", message)

    def success(self, message):
        """Log success message (custom level)"""
        self.logger.info(message)
        self._write_to_gui("SUCCESS", message)

    def critical(self, message):
        """Log critical message"""
        self.logger.critical(message)
        self._write_to_gui("ERROR", message)

    def exception(self, message):
        """Log exception with traceback"""
        self.logger.exception(message)
        self._write_to_gui(f"EXCEPTION: {message}")

    def get_log_file_path(self):
        """Get the current log file path"""
        return self.log_file_path

    def get_all_log_files(self):
        """Get list of all log files"""
        try:
            log_files = []
            for filename in os.listdir(self.log_dir):
                if filename.startswith("driver_updater_") and filename.endswith(".log"):
                    log_files.append(os.path.join(self.log_dir, filename))
            return sorted(log_files, reverse=True)  # Most recent first
        except:
            return []

    def clean_old_logs(self, keep_days=30):
        """Clean up log files older than specified days"""
        try:
            import time

            cutoff_time = time.time() - (keep_days * 24 * 60 * 60)

            cleaned_count = 0
            for log_file in self.get_all_log_files():
                if os.path.getmtime(log_file) < cutoff_time:
                    try:
                        os.remove(log_file)
                        cleaned_count += 1
                    except:
                        pass

            if cleaned_count > 0:
                self.info(f"Cleaned up {cleaned_count} old log files")

        except Exception as e:
            self.warning(f"Error cleaning old logs: {str(e)}")

    def create_session_separator(self):
        """Create a separator in the log for new session"""
        separator = "=" * 80
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session_start = f"NEW SESSION STARTED: {timestamp}"

        self.logger.info(separator)
        self.logger.info(session_start)
        self.logger.info(separator)

        if self.gui_text_widget:
            self._write_to_gui(separator)
            self._write_to_gui(session_start)
            self._write_to_gui(separator)
