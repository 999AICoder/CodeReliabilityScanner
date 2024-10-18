"""This module provides a custom Logger class for consistent logging across the application."""

import logging


class Logger:
    """A custom logger class that provides consistent logging functionality."""

    def __init__(self):
        """Initialize the Logger with a configured logging.Logger instance."""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

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
