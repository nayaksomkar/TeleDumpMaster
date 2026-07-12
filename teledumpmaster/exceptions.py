# Custom exceptions used throughout the application.
# Each inherits from TeleDumpMasterError so callers can catch all app errors.

from __future__ import annotations


class TeleDumpMasterError(Exception):
    """Base exception for all app errors. Catch this to handle any app error."""
    ...


class ConfigurationError(TeleDumpMasterError):
    """Raised when required config is missing or a value is invalid."""
    ...


class UploadError(TeleDumpMasterError):
    """Raised when a Telegram upload fails after exhausting all retries."""
    ...
