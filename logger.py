"""This module provides a custom Logger class for consistent logging across the application."""

import logging
import logging.handlers
from pathlib import Path


class Logger:
    """A custom logger class that provides consistent logging functionality."""

    def __init__(self, log_dir=None, max_bytes=10485760, backup_count=5):
        """Initialize the Logger with a configured logging.Logger instance."""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
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
            log_dir.mkdir(exist_ok=True)
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
