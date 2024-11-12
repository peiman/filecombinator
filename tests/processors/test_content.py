# tests/processors/test_content.py
"""Test suite for ContentProcessor."""

import os
import tempfile
from io import StringIO
from typing import Generator

import pytest

from filecombinator.core.exceptions import FileProcessingError
from filecombinator.processors.content import ContentProcessor


@pytest.fixture
def test_files() -> Generator[dict[str, str], None, None]:
    """Create test files for processing.

    Returns:
        Dictionary with paths to test files
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a text file
        text_file = os.path.join(tmpdir, "test.txt")
        with open(text_file, "w", encoding="utf-8") as f:
            f.write("Test content")

        # Create a binary file
        binary_file = os.path.join(tmpdir, "test.bin")
        with open(binary_file, "wb") as f:
            f.write(b"\x00\x01\x02\x03")

        # Create an image file
        image_file = os.path.join(tmpdir, "test.jpg")
        with open(image_file, "wb") as f:
            f.write(b"JFIF")

        yield {
            "text": text_file,
            "binary": binary_file,
            "image": image_file,
            "dir": tmpdir,
        }


@pytest.fixture
def processor() -> ContentProcessor:
    """Create a ContentProcessor instance."""
    return ContentProcessor()


def test_processor_initialization(processor: ContentProcessor) -> None:
    """Test ContentProcessor initialization."""
    assert processor.stats.processed == 0
    assert processor.stats.binary == 0
    assert processor.stats.image == 0
    assert processor.stats.skipped == 0
    assert len(processor.file_lists.text) == 0
    assert len(processor.file_lists.binary) == 0
    assert len(processor.file_lists.image) == 0


def test_get_file_info(processor: ContentProcessor, test_files: dict[str, str]) -> None:
    """Test file information retrieval."""
    info = processor.get_file_info(test_files["text"])
    assert isinstance(info, dict)
    assert "size" in info
    assert "modified" in info
    assert "type" in info
    assert info["type"] == "Text"


def test_get_file_info_error(processor: ContentProcessor) -> None:
    """Test file info retrieval with nonexistent file."""
    with pytest.raises(FileProcessingError):
        processor.get_file_info("nonexistent.txt")


def test_process_text_file(
    processor: ContentProcessor, test_files: dict[str, str]
) -> None:
    """Test text file processing."""
    output = StringIO()
    processor.process_file(test_files["text"], output)
    content = output.getvalue()

    assert "FILEPATH:" in content
    assert "Test content" in content
    assert "START OF FILE" in content
    assert "END OF FILE" in content
    assert processor.stats.processed == 1
    assert len(processor.file_lists.text) == 1


def test_process_binary_file(
    processor: ContentProcessor, test_files: dict[str, str]
) -> None:
    """Test binary file processing."""
    output = StringIO()
    processor.process_file(test_files["binary"], output)
    content = output.getvalue()

    assert "FILEPATH:" in content
    assert "BINARY FILE (CONTENT EXCLUDED)" in content
    assert processor.stats.binary == 1
    assert len(processor.file_lists.binary) == 1


def test_process_image_file(
    processor: ContentProcessor, test_files: dict[str, str]
) -> None:
    """Test image file processing."""
    output = StringIO()
    processor.process_file(test_files["image"], output)
    content = output.getvalue()

    assert "FILEPATH:" in content
    assert "IMAGE FILE (CONTENT EXCLUDED)" in content
    assert processor.stats.image == 1
    assert len(processor.file_lists.image) == 1


def test_process_nonexistent_file(processor: ContentProcessor) -> None:
    """Test processing a nonexistent file."""
    output = StringIO()
    with pytest.raises(FileProcessingError):
        processor.process_file("nonexistent.txt", output)
    assert processor.stats.skipped == 1


def test_process_unreadable_file(
    processor: ContentProcessor, test_files: dict[str, str]
) -> None:
    """Test processing a file with read permission issues."""
    # Remove read permissions
    os.chmod(test_files["text"], 0o000)
    try:
        output = StringIO()
        with pytest.raises(FileProcessingError):
            processor.process_file(test_files["text"], output)
        assert processor.stats.skipped == 1
    finally:
        # Restore permissions for cleanup
        os.chmod(test_files["text"], 0o666)


def test_stats_increment(processor: ContentProcessor) -> None:
    """Test statistics incrementation."""
    processor._increment_stat("processed")
    processor._increment_stat("binary")
    processor._increment_stat("image")
    processor._increment_stat("skipped")

    assert processor.stats.processed == 1
    assert processor.stats.binary == 1
    assert processor.stats.image == 1
    assert processor.stats.skipped == 1


def test_add_file(processor: ContentProcessor) -> None:
    """Test adding files to tracking lists."""
    processor._add_file("text", "test1.txt")
    processor._add_file("binary", "test2.bin")
    processor._add_file("image", "test3.jpg")

    assert "test1.txt" in processor.file_lists.text
    assert "test2.bin" in processor.file_lists.binary
    assert "test3.jpg" in processor.file_lists.image
