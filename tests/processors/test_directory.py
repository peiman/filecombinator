# tests/processors/test_directory.py
"""Test suite for DirectoryProcessor."""

import os
import tempfile
from pathlib import Path
from typing import Any, Generator, Set

import pytest

from filecombinator.core.exceptions import DirectoryProcessingError
from filecombinator.processors.directory import DirectoryProcessor


@pytest.fixture
def test_directory() -> Generator[dict[str, Any], None, None]:
    """Create a test directory structure.

    Returns:
        Dictionary with test directory information
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some test files and directories
        os.makedirs(os.path.join(tmpdir, "subdir"))
        os.makedirs(os.path.join(tmpdir, "__pycache__"))
        os.makedirs(os.path.join(tmpdir, ".git"))

        with open(os.path.join(tmpdir, "test1.txt"), "w") as f:
            f.write("test1")
        with open(os.path.join(tmpdir, "subdir", "test2.txt"), "w") as f:
            f.write("test2")
        with open(os.path.join(tmpdir, "__pycache__", "test.pyc"), "w") as f:
            f.write("cache")

        yield {
            "path": tmpdir,
            "files": ["test1.txt", "subdir/test2.txt", "__pycache__/test.pyc"],
        }


@pytest.fixture
def processor() -> DirectoryProcessor:
    """Create a DirectoryProcessor instance."""
    exclude_patterns: Set[str] = {"__pycache__", ".git"}
    return DirectoryProcessor(exclude_patterns=exclude_patterns)


def test_directory_processor_initialization(processor: DirectoryProcessor) -> None:
    """Test DirectoryProcessor initialization."""
    assert "__pycache__" in processor.exclude_patterns
    assert ".git" in processor.exclude_patterns


def test_is_excluded(processor: DirectoryProcessor) -> None:
    """Test path exclusion checks."""
    assert processor.is_excluded(Path("__pycache__/test.pyc"))
    assert processor.is_excluded(Path(".git/config"))
    assert not processor.is_excluded(Path("test.txt"))
    assert not processor.is_excluded(Path("subdir/test.txt"))


def test_is_excluded_output_file(processor: DirectoryProcessor) -> None:
    """Test output file exclusion."""
    processor.output_file = "output.txt"
    assert processor.is_excluded(Path("output.txt"))
    assert processor.is_excluded(Path("dir/test_file_combinator_output.txt"))


def test_process_directory(
    processor: DirectoryProcessor, test_directory: dict[str, Any]
) -> None:
    """Test directory processing."""
    processed_files = []

    def callback(file_path: str) -> None:
        processed_files.append(os.path.relpath(file_path, test_directory["path"]))

    processor.process_directory(test_directory["path"], callback)

    assert "test1.txt" in processed_files
    assert "subdir/test2.txt" in processed_files
    assert "__pycache__/test.pyc" not in processed_files


def test_process_directory_error(processor: DirectoryProcessor) -> None:
    """Test directory processing with nonexistent directory."""
    with pytest.raises(DirectoryProcessingError):
        processor.process_directory(
            "nonexistent_directory",
            lambda x: None,
        )


def test_generate_tree(
    processor: DirectoryProcessor, test_directory: dict[str, Any]
) -> None:
    """Test directory tree generation."""

    class MockFile:
        def __init__(self) -> None:
            self.content: list[str] = []

        def write(self, text: str) -> None:
            self.content.append(text)

    mock_file = MockFile()
    processor.generate_tree(test_directory["path"], mock_file)

    content = "".join(mock_file.content)
    assert "DIRECTORY STRUCTURE" in content
    assert "test1.txt" in content
    assert "subdir" in content
    assert "__pycache__" not in content
    assert ".git" not in content


def test_generate_tree_error(processor: DirectoryProcessor) -> None:
    """Test tree generation with invalid directory."""
    with pytest.raises(DirectoryProcessingError):
        processor.generate_tree("nonexistent_directory", None)
