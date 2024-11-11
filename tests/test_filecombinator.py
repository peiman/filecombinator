# tests/test_filecombinator.py
"""Test suite for the FileCombinator class."""

import logging
import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from _pytest.fixtures import FixtureRequest

from filecombinator.filecombinator import FileCombinator, FileCombinatorError


@pytest.fixture
def tmp_path_str() -> Generator[str, None, None]:
    """Create a temporary directory with test files.

    Returns:
        Generator[str, None, None]: Path to temporary directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a text file
        with open(os.path.join(tmpdir, "test.txt"), "w", encoding="utf-8") as f:
            f.write("Test content")

        # Create a "binary" file
        with open(os.path.join(tmpdir, "test.bin"), "wb") as f:
            f.write(b"\x00\x01\x02")

        # Create a subdirectory with a file
        subdir = os.path.join(tmpdir, "subdir")
        os.makedirs(subdir)
        with open(os.path.join(subdir, "subfile.txt"), "w", encoding="utf-8") as f:
            f.write("Subfile content")

        yield tmpdir


@pytest.fixture(name="file_tool")
def fixture_file_tool() -> FileCombinator:
    """Create a FileCombinator instance with test configuration.

    Returns:
        FileCombinator: Configured instance for testing
    """
    return FileCombinator(verbose=True)


def test_initialization(file_tool: FileCombinator) -> None:
    """Test FileCombinator initialization."""
    assert isinstance(file_tool, FileCombinator)
    assert file_tool.verbose is True
    assert "__pycache__" in file_tool.exclude_patterns


def test_is_excluded(file_tool: FileCombinator) -> None:
    """Test file exclusion patterns."""
    assert file_tool.is_excluded(Path("__pycache__/test.py"))
    assert file_tool.is_excluded(Path(".git/config"))
    assert not file_tool.is_excluded(Path("regular_file.txt"))


@pytest.mark.parametrize("test_dir", ["tmp_path_str"])
def test_is_binary_file(
    file_tool: FileCombinator, test_dir: str, request: FixtureRequest
) -> None:
    """Test binary file detection.

    Args:
        file_tool: FileCombinator instance
        test_dir: Name of the fixture providing the test directory
        request: Fixture request object to get the test directory
    """
    tmpdir = request.getfixturevalue(test_dir)
    binary_file = os.path.join(tmpdir, "test.bin")
    text_file = os.path.join(tmpdir, "test.txt")

    assert file_tool.is_binary_file(binary_file)
    assert not file_tool.is_binary_file(text_file)


@pytest.mark.parametrize("test_dir", ["tmp_path_str"])
def test_process_directory(
    file_tool: FileCombinator, test_dir: str, request: FixtureRequest
) -> None:
    """Test directory processing.

    Args:
        file_tool: FileCombinator instance
        test_dir: Name of the fixture providing the test directory
        request: Fixture request object to get the test directory
    """
    tmpdir = request.getfixturevalue(test_dir)
    output_file = os.path.join(tmpdir, "output.txt")
    file_tool.process_directory(tmpdir, output_file)

    assert os.path.exists(output_file)
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "DIRECTORY STRUCTURE" in content
        assert "test.txt" in content
        assert "Test content" in content
        assert "BINARY FILE (CONTENT EXCLUDED)" in content
        assert "subdir" in content
        assert "subfile.txt" in content


@pytest.mark.parametrize("test_dir", ["tmp_path_str"])
def test_file_info(
    file_tool: FileCombinator, test_dir: str, request: FixtureRequest
) -> None:
    """Test file information gathering.

    Args:
        file_tool: FileCombinator instance
        test_dir: Name of the fixture providing the test directory
        request: Fixture request object to get the test directory
    """
    tmpdir = request.getfixturevalue(test_dir)
    text_file = os.path.join(tmpdir, "test.txt")
    info = file_tool.get_file_info(text_file)

    assert isinstance(info, dict)
    assert "size" in info
    assert "modified" in info
    assert "type" in info
    assert info["type"] == "Text"


def test_error_handling(file_tool: FileCombinator) -> None:
    """Test error handling for non-existent files."""
    with pytest.raises(FileCombinatorError) as exc_info:
        file_tool.get_file_info("nonexistent_file.txt")
    assert "Failed to get file info" in str(exc_info.value)


def test_logging_setup() -> None:
    """Test logging configuration."""
    logger = FileCombinator.setup_logging(verbose=True)
    assert logger.level == logging.DEBUG
