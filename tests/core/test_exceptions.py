# tests/core/test_exceptions.py
"""Test suite for FileCombinator exceptions."""

from typing import NoReturn

import pytest

from filecombinator.core.exceptions import (
    ConfigurationError,
    DirectoryProcessingError,
    FileCombinatorError,
    FileProcessingError,
)


def test_file_combinator_error() -> None:
    """Test base FileCombinatorError."""
    with pytest.raises(FileCombinatorError, match="Test error"):
        raise_file_combinator_error()


def raise_file_combinator_error() -> NoReturn:
    """Raise a FileCombinatorError for testing."""
    raise FileCombinatorError("Test error")


def test_file_processing_error() -> None:
    """Test FileProcessingError."""
    with pytest.raises(FileProcessingError, match="Processing failed"):
        raise_file_processing_error()


def raise_file_processing_error() -> NoReturn:
    """Raise a FileProcessingError for testing."""
    raise FileProcessingError("Processing failed")


def test_directory_processing_error() -> None:
    """Test DirectoryProcessingError."""
    with pytest.raises(DirectoryProcessingError, match="Directory error"):
        raise_directory_processing_error()


def raise_directory_processing_error() -> NoReturn:
    """Raise a DirectoryProcessingError for testing."""
    raise DirectoryProcessingError("Directory error")


def test_configuration_error() -> None:
    """Test ConfigurationError."""
    with pytest.raises(ConfigurationError, match="Config error"):
        raise_configuration_error()


def raise_configuration_error() -> NoReturn:
    """Raise a ConfigurationError for testing."""
    raise ConfigurationError("Config error")
