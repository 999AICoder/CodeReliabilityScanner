"""Custom exceptions for the application."""

class AiderTimeoutError(Exception):
    """Raised when Aider process times out."""
    pass

class CodeValidationError(Exception):
    """Raised when code validation fails."""
    pass

class AiderProcessError(Exception):
    """Raised when Aider process fails."""
    pass

class MaxRetriesExceededError(Exception):
    """Raised when maximum retries are exceeded."""
    pass
