# tests/core/test_file_utils_json.py
"""Test suite for JSON file type detection in FileCombinator."""

import json
import logging
from pathlib import Path
from typing import Generator

import pytest

from filecombinator.core.exceptions import FileProcessingError
from filecombinator.core.file_utils import FileTypeDetector

# Set up logging at module level
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def enable_debug_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Enable debug logging for all tests."""
    caplog.set_level(logging.DEBUG)


@pytest.fixture
def temp_files(tmp_path: Path) -> Generator[dict[str, Path], None, None]:
    """Create temporary test files."""
    # Create test files
    test_file = tmp_path / "test.json"
    test_data = {"key": "value", "nested": {"test": True}}
    test_file.write_text(json.dumps(test_data))

    # Create file with null bytes
    null_file = tmp_path / "null.txt"
    null_content = b"Some text\x00with nulls"
    null_file.write_bytes(null_content)
    logger.debug("Created null file at %s with content: %r", null_file, null_content)

    # Create file with invalid UTF-8
    invalid_utf8 = tmp_path / "invalid.txt"
    invalid_content = b"\xff\xfe\x00\x00Invalid UTF-8"
    invalid_utf8.write_bytes(invalid_content)
    logger.debug(
        "Created invalid UTF-8 file at %s with content: %r",
        invalid_utf8,
        invalid_content,
    )

    yield {
        "json": test_file,
        "null": null_file,
        "invalid_utf8": invalid_utf8,
        "dir": tmp_path,
    }


def test_file_with_null_bytes(
    temp_files: dict[str, Path], caplog: pytest.LogCaptureFixture
) -> None:
    """Test detection of files containing null bytes."""
    logger.info("=== Starting null bytes test ===")
    detector = FileTypeDetector()
    null_file = temp_files["null"]

    # Verify content has null bytes
    with open(null_file, "rb") as f:
        content = f.read()
        logger.debug("Reading null file content: %r", content)
        assert b"\x00" in content, "Test file should contain null bytes"

    result = detector.is_binary_file(null_file)
    logger.debug("Binary detection result for null bytes file: %s", result)
    assert result is True, "File with null bytes should be binary"


def test_file_with_invalid_utf8(
    temp_files: dict[str, Path], caplog: pytest.LogCaptureFixture
) -> None:
    """Test detection of files with invalid UTF-8."""
    logger.info("=== Starting invalid UTF-8 test ===")
    detector = FileTypeDetector()
    invalid_file = temp_files["invalid_utf8"]

    # Verify content is invalid UTF-8
    with open(invalid_file, "rb") as f:
        content = f.read()
        logger.debug("Reading invalid UTF-8 file content: %r", content)
        with pytest.raises(UnicodeDecodeError) as exc_info:
            content.decode("utf-8", errors="strict")
        logger.debug("Got expected UnicodeDecodeError: %s", exc_info.value)

    result = detector.is_binary_file(invalid_file)
    logger.debug("Binary detection result for invalid UTF-8 file: %s", result)
    assert result is True, "File with invalid UTF-8 should be binary"


def test_read_error_handling(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Test handling of read errors during binary detection."""
    logger.info("=== Starting read error test ===")
    detector = FileTypeDetector()
    error_file = tmp_path / "error.txt"

    # Create a file but make it unreadable
    error_file.write_text("test")
    error_file.chmod(0o000)
    logger.debug("Created unreadable file at: %s", error_file)
    logger.debug("File permissions: %o", error_file.stat().st_mode)

    try:
        with pytest.raises(FileProcessingError) as exc_info:
            detector.is_binary_file(error_file)
        # Access exc_info.value after the context manager
        logger.debug("Got expected FileProcessingError: %s", exc_info.value)
        assert "Error reading file" in str(exc_info.value)
    except Exception as e:
        logger.error("Unexpected error during test: %s", e, exc_info=True)
        raise
    finally:
        # Restore permissions for cleanup
        error_file.chmod(0o644)
        logger.debug("Restored file permissions for cleanup")
