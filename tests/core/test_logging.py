# tests/core/test_logging.py
"""Test suite for FileCombinator logging functionality."""

import logging
import os
import tempfile
from typing import Generator

import pytest

from filecombinator.core.logging import setup_logging


@pytest.fixture
def clean_logging() -> Generator[None, None, None]:
    """Reset logging configuration after each test."""
    yield
    # Reset root logger
    logger = logging.getLogger()
    logger.handlers = []
    logger.setLevel(logging.WARNING)


@pytest.mark.usefixtures("clean_logging")
def test_setup_logging() -> None:
    """Test logging setup."""
    logger = setup_logging(verbose=True)
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) > 0
    assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)


@pytest.mark.usefixtures("clean_logging")
def test_setup_logging_with_file() -> None:
    """Test logging setup with file output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "test.log")
        logger = setup_logging(log_file, verbose=True)

        assert logger.level == logging.DEBUG
        assert len(logger.handlers) > 1  # Console and file handlers
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
        assert any(
            isinstance(h, logging.handlers.RotatingFileHandler) for h in logger.handlers
        )

        # Verify log file was created
        assert os.path.exists(log_file)


@pytest.mark.usefixtures("clean_logging")
def test_setup_logging_without_file() -> None:
    """Test logging setup without file output."""
    logger = setup_logging(verbose=False)
    assert logger.level == logging.INFO
    assert len(logger.handlers) == 1  # Only console handler
    assert isinstance(logger.handlers[0], logging.StreamHandler)


@pytest.mark.usefixtures("clean_logging")
def test_setup_logging_formatter() -> None:
    """Test logging formatters are correctly set up."""
    logger = setup_logging(verbose=True)

    for handler in logger.handlers:
        formatter = handler.formatter
        assert formatter is not None, "Formatter should not be None"
        fmt = formatter._fmt
        assert fmt is not None, "Format string should not be None"

        if isinstance(handler, logging.StreamHandler) and not isinstance(
            handler, logging.handlers.RotatingFileHandler
        ):
            # Simple formatter for console
            assert "%(levelname)s: %(message)s" == fmt
        elif isinstance(handler, logging.handlers.RotatingFileHandler):
            # Detailed formatter for file
            assert "%(asctime)s" in str(fmt)
            assert "%(name)s" in str(fmt)
            assert "%(levelname)s" in str(fmt)
            assert "%(message)s" in str(fmt)
