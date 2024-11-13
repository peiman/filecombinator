# tests/processors/test_directory.py
"""Test suite for DirectoryProcessor."""

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Generator, Set

import pytest

from filecombinator.core.exceptions import DirectoryProcessingError
from filecombinator.processors.directory import DirectoryProcessor

logger = logging.getLogger(__name__)


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
    tree_content = processor.generate_tree(test_directory["path"])

    # Verify tree structure
    assert "test1.txt" in tree_content
    assert "subdir" in tree_content
    assert "__pycache__" not in tree_content
    assert ".git" not in tree_content

    # Verify tree formatting
    assert "├── " in tree_content or "└── " in tree_content
    assert "│   " in tree_content


def test_generate_tree_empty_directory() -> None:
    """Test tree content generation with empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        processor = DirectoryProcessor(set())
        tree_content = processor.generate_tree(tmpdir)
        assert tree_content == ""


def test_generate_tree_single_file() -> None:
    """Test tree content generation with a single file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a single test file
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")

        processor = DirectoryProcessor(set())
        tree_content = processor.generate_tree(tmpdir)
        assert "└── test.txt" in tree_content


def test_generate_tree_nested_directories() -> None:
    """Test tree content generation with nested directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create nested directory structure with multiple paths to force vertical lines
        os.makedirs(os.path.join(tmpdir, "dir1", "dir2"))
        os.makedirs(os.path.join(tmpdir, "dir1", "dir3"))  # Add sibling directory

        # Add files in different directories
        with open(os.path.join(tmpdir, "dir1", "dir2", "test1.txt"), "w") as f:
            f.write("test1")
        with open(os.path.join(tmpdir, "dir1", "dir3", "test2.txt"), "w") as f:
            f.write("test2")

        processor = DirectoryProcessor(set())
        tree_content = processor.generate_tree(tmpdir)

        # Output should look like:
        # tmpXXX
        # └── dir1
        #     ├── dir2
        #     │   └── test1.txt
        #     └── dir3
        #         └── test2.txt

        assert "dir1" in tree_content
        assert "dir2" in tree_content
        assert "dir3" in tree_content
        assert "test1.txt" in tree_content
        assert "test2.txt" in tree_content
        assert "├── " in tree_content  # Has branching
        assert "│   " in tree_content  # Has vertical line


def test_generate_tree_error(processor: DirectoryProcessor) -> None:
    """Test tree generation with nonexistent directory."""
    with pytest.raises(DirectoryProcessingError):
        processor.generate_tree("nonexistent_directory")


def test_process_directory_error_processing_file(tmp_path: Path) -> None:
    """Test handling of errors during file processing."""
    # Create a processor
    processor = DirectoryProcessor(set())

    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    # Create a callback that raises an error
    def failing_callback(file_path: str) -> None:
        raise OSError("Test error processing file")

    # Ensure the error is propagated properly
    with pytest.raises(DirectoryProcessingError) as exc_info:
        processor.process_directory(str(tmp_path), failing_callback)

    assert "Test error processing file" in str(exc_info.value)
    assert "Failed to process directory" in str(exc_info.value)


def test_process_directory_with_subdirectories(tmp_path: Path) -> None:
    """Test processing directory with subdirectories and files."""
    # Create a test directory structure
    subdir = tmp_path / "subdir"
    subdir.mkdir()

    (tmp_path / "file1.txt").write_text("test1")
    (subdir / "file2.txt").write_text("test2")

    # Track processed files
    processed_files = []

    def callback(file_path: str) -> None:
        processed_files.append(os.path.basename(file_path))

    # Process directory
    processor = DirectoryProcessor(set())
    processor.process_directory(str(tmp_path), callback)

    # Verify both files were processed in sorted order
    assert processed_files == ["file1.txt", "file2.txt"]


def test_process_directory_with_empty_subdirectories(tmp_path: Path) -> None:
    """Test processing directory with empty subdirectories."""
    # Create empty subdirectories
    (tmp_path / "empty1").mkdir()
    (tmp_path / "empty2").mkdir()

    # Add one file to make sure processing happens
    (tmp_path / "test.txt").write_text("test")

    processed_files = []

    def callback(file_path: str) -> None:
        processed_files.append(os.path.basename(file_path))

    processor = DirectoryProcessor(set())
    processor.process_directory(str(tmp_path), callback)

    # Only the text file should be processed
    assert processed_files == ["test.txt"]
