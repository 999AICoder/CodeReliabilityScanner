"""This module provides a custom Logger class for consistent logging across the application."""

import logging
import logging.handlers
import time
from pathlib import Path


class Logger:
    """A custom logger class that provides consistent logging functionality."""

    def __init__(self, log_dir=None, max_bytes=10485760, backup_count=5):
        """Initialize the Logger with a configured logging.Logger instance."""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        self.logger.handlers = []
        
        # Always add stream handler
        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] %(message)s'
        )
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)
        
        # Add file handler if log_dir is specified
        if log_dir:
            log_dir = Path(log_dir)
            try:
                log_dir.mkdir(exist_ok=True, parents=True)
            except Exception as e:
                print(f"Warning: Could not create log directory {log_dir}: {e}")
                return
            file_handler = logging.handlers.RotatingFileHandler(
                log_dir / 'app.log',
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def info(self, message: str) -> None:
        """
        Log an info level message.

        Args:
            message (str): The message to be logged.
        """
        self.logger.info(message)

    def error(self, message: str) -> None:
        """
        Log an error level message.

        Args:
            message (str): The error message to be logged.
        """
        self.logger.error(message)

    @staticmethod
    def cleanup_old_logs(log_dir: str, max_age_days: int = 30) -> None:
        """
        Clean up log files older than max_age_days.

        Args:
            log_dir (str): Directory containing log files
            max_age_days (int): Maximum age of log files in days
        """
        log_path = Path(log_dir)
        if not log_path.exists():
            return
            
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 3600
        
        for log_file in log_path.glob("*.log*"):
            file_age = current_time - log_file.stat().st_mtime
            if file_age > max_age_seconds:
                log_file.unlink()
