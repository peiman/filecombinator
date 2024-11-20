# tests/processors/test_content.py
"""Test suite for ContentProcessor."""

import io
import logging
import os
from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest

from filecombinator.core.exceptions import FileProcessingError
from filecombinator.processors.content import ContentProcessor

# Set up logging at module level
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@pytest.fixture
def test_files(tmp_path: Path) -> Generator[dict[str, Path], None, None]:
    """Create test files for processing.

    Returns:
        Dictionary with paths to test files
    """
    # Create various test files
    text_file = tmp_path / "test.txt"
    text_file.write_text("Test content")

    binary_file = tmp_path / "test.bin"
    binary_file.write_bytes(b"\x00\x01\x02\x03")

    image_file = tmp_path / "test.jpg"
    image_file.write_bytes(b"JFIF")  # Fake JPEG header

    # Create files with special content
    unicode_file = tmp_path / "unicode.txt"
    unicode_file.write_text("Unicode ♥ content ☺")

    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")  # Create as text file

    # Create a directory for path testing
    nested_dir = tmp_path / "nested"
    nested_dir.mkdir()
    nested_file = nested_dir / "nested.txt"
    nested_file.write_text("Nested content")

    yield {
        "text": text_file,
        "binary": binary_file,
        "image": image_file,
        "unicode": unicode_file,
        "empty": empty_file,
        "nested": nested_file,
        "dir": nested_dir,
    }


def test_processor_initialization() -> None:
    """Test ContentProcessor initialization."""
    processor = ContentProcessor()
    assert processor.stats.processed == 0
    assert processor.stats.binary == 0
    assert processor.stats.image == 0
    assert processor.stats.skipped == 0
    assert len(processor.file_lists.text) == 0
    assert len(processor.file_lists.binary) == 0
    assert len(processor.file_lists.image) == 0


def test_track_file_text(test_files: dict[str, Path]) -> None:
    """Test tracking of text files."""
    processor = ContentProcessor()
    file_path = str(test_files["text"])

    processor.track_file(file_path)

    assert processor.stats.processed == 1
    assert processor.stats.binary == 0
    assert processor.stats.image == 0
    assert len(processor.file_lists.text) == 1
    assert file_path in processor.file_lists.text


def test_track_file_binary(test_files: dict[str, Path]) -> None:
    """Test tracking of binary files."""
    processor = ContentProcessor()
    file_path = str(test_files["binary"])

    processor.track_file(file_path)

    assert processor.stats.processed == 0
    assert processor.stats.binary == 1
    assert processor.stats.image == 0
    assert len(processor.file_lists.binary) == 1
    assert file_path in processor.file_lists.binary


def test_track_file_image(test_files: dict[str, Path]) -> None:
    """Test tracking of image files."""
    processor = ContentProcessor()
    file_path = str(test_files["image"])

    processor.track_file(file_path)

    assert processor.stats.processed == 0
    assert processor.stats.binary == 0
    assert processor.stats.image == 1
    assert len(processor.file_lists.image) == 1
    assert file_path in processor.file_lists.image


def test_track_file_nonexistent() -> None:
    """Test tracking of nonexistent file."""
    processor = ContentProcessor()
    processor.track_file("nonexistent.txt")
    assert processor.stats.skipped == 1


def test_track_multiple_files(test_files: dict[str, Path]) -> None:
    """Test tracking multiple files."""
    processor = ContentProcessor()

    processor.track_file(str(test_files["text"]))
    processor.track_file(str(test_files["binary"]))
    processor.track_file(str(test_files["image"]))

    assert processor.stats.processed == 1
    assert processor.stats.binary == 1
    assert processor.stats.image == 1
    assert len(processor.file_lists.text) == 1
    assert len(processor.file_lists.binary) == 1
    assert len(processor.file_lists.image) == 1


def test_track_same_file_twice(test_files: dict[str, Path]) -> None:
    """Test tracking the same file multiple times."""
    processor = ContentProcessor()

    processor.track_file(str(test_files["text"]))
    processor.track_file(str(test_files["text"]))

    assert processor.stats.processed == 2
    assert len(processor.file_lists.text) == 2


def test_process_text_file(test_files: dict[str, Path]) -> None:
    """Test processing a text file."""
    processor = ContentProcessor()
    output = io.StringIO()

    processor.process_file(str(test_files["text"]), output)

    content = output.getvalue()
    assert "Test content" in content
    assert "Type: Text" in content


def test_process_binary_file(test_files: dict[str, Path]) -> None:
    """Test processing a binary file."""
    processor = ContentProcessor()
    output = io.StringIO()

    processor.process_file(str(test_files["binary"]), output)

    content = output.getvalue()
    assert "BINARY FILE (CONTENT EXCLUDED)" in content
    assert "Type: Binary" in content


def test_process_image_file(test_files: dict[str, Path]) -> None:
    """Test processing an image file."""
    processor = ContentProcessor()
    output = io.StringIO()

    processor.process_file(str(test_files["image"]), output)

    content = output.getvalue()
    assert "IMAGE FILE (CONTENT EXCLUDED)" in content
    assert "Type: Image" in content


def test_process_unicode_file(test_files: dict[str, Path]) -> None:
    """Test processing a file with unicode content."""
    processor = ContentProcessor()
    output = io.StringIO()

    processor.process_file(str(test_files["unicode"]), output)

    content = output.getvalue()
    assert "Unicode ♥ content ☺" in content
    assert "Type: Text" in content


def test_process_empty_file(test_files: dict[str, Path]) -> None:
    """Test processing an empty file."""
    processor = ContentProcessor()
    output = io.StringIO()

    processor.process_file(str(test_files["empty"]), output)

    content = output.getvalue()
    assert "Size: 0 bytes" in content
    # An empty file should be treated as text
    assert "Type: Text" in content


def test_process_nested_file(test_files: dict[str, Path]) -> None:
    """Test processing a file in a nested directory."""
    processor = ContentProcessor()
    output = io.StringIO()

    processor.process_file(str(test_files["nested"]), output)

    content = output.getvalue()
    assert "Nested content" in content
    assert "Type: Text" in content


def test_process_nonexistent_file() -> None:
    """Test processing a nonexistent file."""
    processor = ContentProcessor()
    output = io.StringIO()

    with pytest.raises(FileProcessingError) as exc_info:
        processor.process_file("nonexistent.txt", output)

    assert "No such file or directory" in str(exc_info.value)


def test_process_unreadable_file(test_files: dict[str, Path]) -> None:
    """Test processing a file that can't be read."""
    processor = ContentProcessor()
    output = io.StringIO()

    # Make file unreadable
    file_path = test_files["text"]
    os.chmod(file_path, 0o000)

    try:
        with pytest.raises(FileProcessingError) as exc_info:
            processor.process_file(str(file_path), output)
        error_msg = str(exc_info.value)
        logger.debug("Caught error message: %s", error_msg)
        assert (
            "Permission denied" in error_msg or "Error reading file" in error_msg
        ), f"Unexpected error message: {error_msg}"
    finally:
        # Restore permissions for cleanup
        os.chmod(file_path, 0o644)


def test_file_info_error(test_files: dict[str, Path]) -> None:
    """Test handling of file info errors."""
    processor = ContentProcessor()

    with patch("os.stat") as mock_stat:
        mock_stat.side_effect = OSError("Test error")
        with pytest.raises(FileProcessingError) as exc_info:
            processor.get_file_info(str(test_files["text"]))

    assert "Failed to get file info" in str(exc_info.value)


def test_get_file_info_success(test_files: dict[str, Path]) -> None:
    """Test successful file info retrieval."""
    processor = ContentProcessor()

    info = processor.get_file_info(str(test_files["text"]))

    assert isinstance(info, dict)
    assert "size" in info
    assert "modified" in info
    assert "type" in info
    assert info["type"] == "Text"


def test_process_file_with_unicode_error(test_files: dict[str, Path]) -> None:
    """Test handling of Unicode decoding errors."""
    processor = ContentProcessor()
    output = io.StringIO()

    with patch("builtins.open") as mock_file:
        mock_file.side_effect = UnicodeDecodeError("utf-8", b"test", 0, 1, "test error")
        with pytest.raises(FileProcessingError) as exc_info:
            processor.process_file(str(test_files["text"]), output)

    assert "test error" in str(exc_info.value)
