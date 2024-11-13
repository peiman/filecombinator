# tests/processors/test_content.py
"""Test suite for ContentProcessor."""

import os
import tempfile
from typing import Generator

import pytest

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


def test_track_file_text(test_files: dict[str, str]) -> None:
    """Test tracking of text files."""
    processor = ContentProcessor()

    processor.track_file(test_files["text"])

    assert processor.stats.processed == 1
    assert processor.stats.binary == 0
    assert processor.stats.image == 0
    assert len(processor.file_lists.text) == 1
    assert test_files["text"] in processor.file_lists.text


def test_track_file_binary(test_files: dict[str, str]) -> None:
    """Test tracking of binary files."""
    processor = ContentProcessor()

    processor.track_file(test_files["binary"])

    assert processor.stats.processed == 0
    assert processor.stats.binary == 1
    assert processor.stats.image == 0
    assert len(processor.file_lists.binary) == 1
    assert test_files["binary"] in processor.file_lists.binary


def test_track_file_image(test_files: dict[str, str]) -> None:
    """Test tracking of image files."""
    processor = ContentProcessor()

    processor.track_file(test_files["image"])

    assert processor.stats.processed == 0
    assert processor.stats.binary == 0
    assert processor.stats.image == 1
    assert len(processor.file_lists.image) == 1
    assert test_files["image"] in processor.file_lists.image


def test_track_file_nonexistent() -> None:
    """Test tracking of nonexistent file."""
    processor = ContentProcessor()

    processor.track_file("nonexistent.txt")

    assert processor.stats.skipped == 1
    assert processor.stats.processed == 0
    assert processor.stats.binary == 0
    assert processor.stats.image == 0


def test_track_multiple_files(test_files: dict[str, str]) -> None:
    """Test tracking of multiple files."""
    processor = ContentProcessor()

    processor.track_file(test_files["text"])
    processor.track_file(test_files["binary"])
    processor.track_file(test_files["image"])

    assert processor.stats.processed == 1
    assert processor.stats.binary == 1
    assert processor.stats.image == 1
    assert len(processor.file_lists.text) == 1
    assert len(processor.file_lists.binary) == 1
    assert len(processor.file_lists.image) == 1


def test_track_same_file_twice(test_files: dict[str, str]) -> None:
    """Test tracking the same file multiple times."""
    processor = ContentProcessor()

    processor.track_file(test_files["text"])
    processor.track_file(test_files["text"])

    assert processor.stats.processed == 2  # Stats increment each time
    assert len(processor.file_lists.text) == 2  # File list grows
