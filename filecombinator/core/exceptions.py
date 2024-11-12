# filecombinator/core/exceptions.py
"""Exceptions for the FileCombinator package."""


class FileCombinatorError(Exception):
    """Base exception for FileCombinator errors."""

    pass


class FileProcessingError(FileCombinatorError):
    """Raised when there's an error processing a file."""

    pass


class DirectoryProcessingError(FileCombinatorError):
    """Raised when there's an error processing a directory."""

    pass


class ConfigurationError(FileCombinatorError):
    """Raised when there's an error in configuration."""

    pass
