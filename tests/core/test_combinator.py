# tests/core/test_combinator.py
"""Test suite for the core FileCombinator class."""

import os
import tempfile
from typing import Generator

import pytest

from filecombinator.core.combinator import FileCombinator
from filecombinator.core.exceptions import FileCombinatorError


@pytest.fixture
def test_directory() -> Generator[str, None, None]:
    """Create a test directory with various file types.

    Returns:
        Path to test directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create regular files
        with open(os.path.join(tmpdir, "text1.txt"), "w", encoding="utf-8") as f:
            f.write("Text file 1")
        with open(os.path.join(tmpdir, "text2.txt"), "w", encoding="utf-8") as f:
            f.write("Text file 2")

        # Create binary and image files
        with open(os.path.join(tmpdir, "binary.bin"), "wb") as f:
            f.write(b"\x00\x01\x02\x03")
        with open(os.path.join(tmpdir, "image.jpg"), "wb") as f:
            f.write(b"JFIF")

        # Create excluded directories and files
        os.makedirs(os.path.join(tmpdir, "__pycache__"))
        os.makedirs(os.path.join(tmpdir, "subdir"))
        with open(os.path.join(tmpdir, "__pycache__", "cache.pyc"), "w") as f:
            f.write("cache")
        with open(os.path.join(tmpdir, "subdir", "text3.txt"), "w") as f:
            f.write("Text file 3")

        yield tmpdir


@pytest.fixture
def combinator() -> FileCombinator:
    """Create a FileCombinator instance."""
    return FileCombinator(verbose=True)


def test_initialization(combinator: FileCombinator) -> None:
    """Test FileCombinator initialization."""
    assert combinator.verbose is True
    assert combinator.output_file is None
    assert "__pycache__" in combinator.exclude_patterns
    assert combinator.directory_processor is not None
    assert combinator.content_processor is not None


def test_initialization_with_additional_excludes() -> None:
    """Test initialization with additional exclude patterns."""
    additional_excludes = {"custom_exclude", "another_exclude"}
    combinator = FileCombinator(additional_excludes=additional_excludes)

    assert "custom_exclude" in combinator.exclude_patterns
    assert "another_exclude" in combinator.exclude_patterns
    assert "__pycache__" in combinator.exclude_patterns  # Default still included


def test_process_directory(combinator: FileCombinator, test_directory: str) -> None:
    """Test directory processing."""
    output_file = os.path.join(test_directory, "output.txt")
    combinator.process_directory(test_directory, output_file)

    assert os.path.exists(output_file)
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "## Directory Structure" in content
        assert "```" in content  # Tree should be in code block


def test_process_nonexistent_directory(combinator: FileCombinator) -> None:
    """Test processing a nonexistent directory."""
    with pytest.raises(FileCombinatorError):
        combinator.process_directory("nonexistent", "output.txt")


def test_process_directory_with_existing_output(
    combinator: FileCombinator, test_directory: str
) -> None:
    """Test processing with existing output file."""
    output_file = os.path.join(test_directory, "output.txt")

    # Create existing output file with some content
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("Existing content")

    # Configure combinator with output file for proper exclusion
    combinator.output_file = output_file

    # Process directory (should overwrite)
    combinator.process_directory(test_directory, output_file)

    # Verify new content
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Existing content" not in content
        assert "output.txt" not in content  # Should not be in directory tree
        assert (
            "## Directory Structure" in content
        )  # Shows structure with proper heading
        assert "```" in content  # Tree should be in code block


def test_statistics_tracking(combinator: FileCombinator, test_directory: str) -> None:
    """Test statistics tracking during processing."""
    output_file = os.path.join(test_directory, "output.txt")
    combinator.process_directory(test_directory, output_file)

    stats = combinator.stats
    assert stats.processed > 0  # Text files
    assert stats.binary > 0  # Binary files
    assert stats.image > 0  # Image files
    assert stats.skipped == 0  # No errors


def test_file_list_tracking(combinator: FileCombinator, test_directory: str) -> None:
    """Test file list tracking during processing."""
    output_file = os.path.join(test_directory, "output.txt")
    combinator.process_directory(test_directory, output_file)

    file_lists = combinator.file_lists
    assert len(file_lists.text) > 0
    assert len(file_lists.binary) > 0
    assert len(file_lists.image) > 0
    assert any("text1.txt" in f for f in file_lists.text)
    assert any("binary.bin" in f for f in file_lists.binary)
    assert any("image.jpg" in f for f in file_lists.image)
