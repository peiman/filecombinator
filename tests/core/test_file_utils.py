# tests/core/test_file_utils.py
"""Test suite for FileCombinator file utilities."""

import os
import tempfile
from typing import Generator

import magic
import pytest

from filecombinator.core.exceptions import FileProcessingError
from filecombinator.core.file_utils import FileTypeDetector, SafeOpen


@pytest.fixture
def temp_files() -> Generator[dict[str, str], None, None]:
    """Create temporary test files.

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
            f.write(b"JFIF")  # Simple JPEG header simulation

        # Create XML file
        xml_file = os.path.join(tmpdir, "test.xml")
        with open(xml_file, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0"?><root></root>')

        # Create JSON file
        json_file = os.path.join(tmpdir, "test.json")
        with open(json_file, "w", encoding="utf-8") as f:
            f.write('{"key": "value"}')

        yield {
            "text": text_file,
            "binary": binary_file,
            "image": image_file,
            "xml": xml_file,
            "json": json_file,
            "dir": tmpdir,
        }


def test_safe_open_text(temp_files: dict[str, str]) -> None:
    """Test SafeOpen with text files."""
    with SafeOpen(temp_files["text"], "r") as f:
        content = f.read()
        assert content == "Test content"


def test_safe_open_binary(temp_files: dict[str, str]) -> None:
    """Test SafeOpen with binary files."""
    with SafeOpen(temp_files["binary"], "rb") as f:
        content = f.read()
        assert content == b"\x00\x01\x02\x03"


def test_safe_open_nonexistent() -> None:
    """Test SafeOpen with nonexistent file."""
    with pytest.raises(IOError):
        with SafeOpen("nonexistent.txt", "r"):
            pass


def test_safe_open_with_custom_encoding(temp_files: dict[str, str]) -> None:
    """Test SafeOpen with custom encoding."""
    with SafeOpen(temp_files["text"], "r", encoding="ascii") as f:
        content = f.read()
        assert content == "Test content"


def test_safe_open_context_manager_exception_handling(
    temp_files: dict[str, str]
) -> None:
    """Test SafeOpen context manager exception handling."""
    file_obj = None
    try:
        with SafeOpen(temp_files["text"], "r") as f:
            file_obj = f
            assert not f.closed  # File should be open within the context
            raise ValueError("Test exception")
    except ValueError:
        assert file_obj is not None
        assert (
            file_obj.closed
        )  # File should be closed after context, even with exception


def test_file_type_detector_initialization() -> None:
    """Test FileTypeDetector initialization."""
    detector = FileTypeDetector()
    assert isinstance(detector.IMAGE_EXTENSIONS, set)
    assert isinstance(detector.BINARY_EXTENSIONS, set)
    assert ".jpg" in detector.IMAGE_EXTENSIONS
    assert ".exe" in detector.BINARY_EXTENSIONS


def test_is_image_file(temp_files: dict[str, str]) -> None:
    """Test image file detection."""
    detector = FileTypeDetector()
    assert detector.is_image_file(temp_files["image"])
    assert not detector.is_image_file(temp_files["text"])
    assert not detector.is_image_file(temp_files["binary"])


def test_is_binary_file(temp_files: dict[str, str]) -> None:
    """Test binary file detection."""
    detector = FileTypeDetector()
    assert detector.is_binary_file(temp_files["binary"])
    assert not detector.is_binary_file(temp_files["text"])


def test_binary_detection_error() -> None:
    """Test binary detection with nonexistent file."""
    detector = FileTypeDetector()
    with pytest.raises(FileProcessingError):
        detector.is_binary_file("nonexistent.bin")


def test_is_binary_file_with_magic_error(
    temp_files: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test binary file detection when magic raises an error."""

    def mock_from_file(*args: str, **kwargs: str) -> None:
        raise IOError("Magic error")

    detector = FileTypeDetector()
    monkeypatch.setattr(detector.mime, "from_file", mock_from_file)

    # Should fall back to alternative detection method
    result = detector.is_binary_file(temp_files["binary"])
    assert result is True


def test_is_binary_file_without_magic(
    temp_files: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test binary file detection without magic library."""
    monkeypatch.setattr("filecombinator.core.file_utils.MAGIC_AVAILABLE", False)
    detector = FileTypeDetector()
    assert detector.is_binary_file(temp_files["binary"])


def test_xml_json_detection(temp_files: dict[str, str]) -> None:
    """Test detection of XML and JSON files as text."""
    detector = FileTypeDetector()
    assert not detector.is_binary_file(temp_files["xml"])
    assert not detector.is_binary_file(temp_files["json"])


def test_mime_initialization_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test FileTypeDetector initialization when magic fails."""

    def mock_magic_init(*args: str, **kwargs: str) -> None:
        raise IOError("Magic initialization error")

    monkeypatch.setattr(magic.Magic, "__init__", mock_magic_init)
    detector = FileTypeDetector()
    assert detector.mime is None
