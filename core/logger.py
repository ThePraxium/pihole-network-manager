"""
Unified session logger for Pi-hole Network Manager

Provides comprehensive logging for the entire main.py execution lifecycle:
- Menu selections and user inputs
- SSH commands and their output
- Status messages (info, success, error, warning)
- File transfer progress and verification
- Exceptions and stack traces

Log file format: YYYYMMDD-HHMMSS.log
Log location: <project-root>/logs/
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import traceback
import threading


class SessionLogger:
    """
    Singleton session logger that captures all events during main.py execution.

    Usage:
        # Initialize at main.py start
        logger = SessionLogger.get_instance()
        logger.start()

        # Log events
        logger.log_menu("Main Menu", "1")
        logger.log_ssh("pihole status", "Active", "", True)
        logger.log_status("info", "Processing...")

        # Stop at main.py exit
        logger.stop()
    """

    _instance: Optional['SessionLogger'] = None
    _lock = threading.Lock()

    def __init__(self, log_dir: Optional[Path] = None):
        """
        Initialize session logger.

        Args:
            log_dir: Directory for log files (default: <project-root>/logs/)
        """
        if log_dir is None:
            # Auto-detect project root (where main.py is located)
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent  # Go up from core/ to project root
            log_dir = project_root / "logs"

        self.log_dir = Path(log_dir)
        self.log_file: Optional[Path] = None
        self._file_handle: Optional[object] = None
        self._active = False
        self._session_start: Optional[datetime] = None

    @classmethod
    def get_instance(cls, log_dir: Optional[Path] = None) -> 'SessionLogger':
        """
        Get singleton instance of SessionLogger.

        Args:
            log_dir: Directory for log files (only used on first call)

        Returns:
            SessionLogger instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(log_dir)
        return cls._instance

    def start(self) -> bool:
        """
        Start logging session.

        Creates log directory if needed and opens log file.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create logs directory
            self.log_dir.mkdir(parents=True, exist_ok=True)

            # Create log file with timestamp
            self._session_start = datetime.now()
            timestamp = self._session_start.strftime("%Y%m%d-%H%M%S")
            self.log_file = self.log_dir / f"{timestamp}.log"

            # Open file handle
            self._file_handle = open(self.log_file, 'w', encoding='utf-8')
            self._active = True

            # Write header
            self._write_header()

            return True

        except Exception as e:
            print(f"Failed to start logger: {e}", file=sys.stderr)
            self._active = False
            return False

    def stop(self):
        """Stop logging session and close file handle."""
        if self._active and self._file_handle:
            try:
                self._write_footer()
                self._file_handle.close()
                self._active = False
                self._file_handle = None
            except Exception as e:
                print(f"Error stopping logger: {e}", file=sys.stderr)

    def is_active(self) -> bool:
        """Check if logger is currently active."""
        return self._active

    def _write_header(self):
        """Write log file header."""
        if not self._file_handle:
            return

        header = f"""
{'='*80}
Pi-hole Network Manager - Session Log
{'='*80}
Session Start: {self._session_start.strftime('%Y-%m-%d %H:%M:%S')}
Log File: {self.log_file.name}
{'='*80}

"""
        self._file_handle.write(header)
        self._file_handle.flush()

    def _write_footer(self):
        """Write log file footer."""
        if not self._file_handle or not self._session_start:
            return

        session_end = datetime.now()
        duration = session_end - self._session_start

        footer = f"""
{'='*80}
Session End: {session_end.strftime('%Y-%m-%d %H:%M:%S')}
Duration: {duration}
{'='*80}
"""
        self._file_handle.write(footer)
        self._file_handle.flush()

    def _write(self, message: str):
        """
        Write message to log file with timestamp.

        Args:
            message: Message to write
        """
        if not self._active or not self._file_handle:
            return

        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            self._file_handle.write(f"[{timestamp}] {message}\n")
            self._file_handle.flush()
        except Exception as e:
            print(f"Error writing to log: {e}", file=sys.stderr)

    def log_menu(self, menu_name: str, choice: str):
        """
        Log menu selection.

        Args:
            menu_name: Name of the menu
            choice: User's choice
        """
        self._write(f"[MENU] {menu_name} -> Choice: {choice}")

    def log_input(self, prompt: str, value: str, masked: bool = False):
        """
        Log user input.

        Args:
            prompt: Input prompt shown to user
            value: User's input value
            masked: Whether to mask the value (e.g., for passwords)
        """
        display_value = "***MASKED***" if masked else value
        self._write(f"[INPUT] {prompt} = {display_value}")

    def log_ssh(self, command: str, stdout: str, stderr: str, success: bool):
        """
        Log SSH command execution.

        Args:
            command: SSH command executed
            stdout: Command stdout
            stderr: Command stderr
            success: Whether command succeeded
        """
        status = "SUCCESS" if success else "FAILED"
        self._write(f"[SSH] {status}: {command}")

        if stdout:
            for line in stdout.strip().split('\n'):
                self._write(f"[SSH:STDOUT]   {line}")

        if stderr:
            for line in stderr.strip().split('\n'):
                self._write(f"[SSH:STDERR]   {line}")

    def log_status(self, level: str, message: str):
        """
        Log status message.

        Args:
            level: Status level (info, success, warning, error)
            message: Status message
        """
        level_upper = level.upper()
        self._write(f"[{level_upper}] {message}")

    def log_transfer(self, action: str, details: str):
        """
        Log file transfer action.

        Args:
            action: Transfer action (upload, download, verify, etc.)
            details: Action details
        """
        self._write(f"[TRANSFER:{action.upper()}] {details}")

    def log_state(self, action: str, step: str, value: any):
        """
        Log state change.

        Args:
            action: State action (mark_complete, reset, etc.)
            step: Setup step name
            value: New value
        """
        self._write(f"[STATE:{action.upper()}] {step} = {value}")

    def log_exception(self, exception: Exception, context: str = ""):
        """
        Log exception with full stack trace.

        Args:
            exception: Exception object
            context: Optional context description
        """
        self._write(f"[EXCEPTION] {context}")
        self._write(f"[EXCEPTION] {type(exception).__name__}: {str(exception)}")

        # Write stack trace
        tb_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
        for line in tb_lines:
            for subline in line.strip().split('\n'):
                self._write(f"[EXCEPTION]   {subline}")

    def log_config(self, action: str, key: str, value: str, masked: bool = False):
        """
        Log configuration change.

        Args:
            action: Config action (set, get, delete)
            key: Configuration key
            value: Configuration value
            masked: Whether to mask the value
        """
        display_value = "***MASKED***" if masked else value
        self._write(f"[CONFIG:{action.upper()}] {key} = {display_value}")

    def log_separator(self, title: str = ""):
        """
        Write visual separator to log.

        Args:
            title: Optional title for the separator
        """
        if title:
            self._write(f"\n{'-'*80}")
            self._write(f"  {title}")
            self._write(f"{'-'*80}")
        else:
            self._write(f"{'-'*80}")

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is not None:
            self.log_exception(exc_val, context="Unhandled exception during session")
        self.stop()


# Global convenience function
def get_logger() -> SessionLogger:
    """
    Get global logger instance.

    Returns:
        SessionLogger instance
    """
    return SessionLogger.get_instance()
