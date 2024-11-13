# tests/test_cleanup.py
"""Test suite for verifying proper cleanup of temporary files."""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from click.testing import CliRunner

from filecombinator.cli import main
from filecombinator.core.combinator import _temp_manager
from filecombinator.core.config import get_config


@pytest.fixture
def config_suffix() -> str:
    """Get the configured output file suffix."""
    return get_config().output_suffix


@pytest.fixture(autouse=True)
def cleanup_temp_files() -> Generator[None, None, None]:
    """Fixture to ensure temporary files are cleaned up after each test."""
    # Store the original tempdir
    original_tempdir = tempfile.tempdir

    # Record initial state of temp directory
    temp_dir = tempfile.gettempdir()
    suffix = get_config().output_suffix
    before_test = {
        os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if suffix in f
    }

    yield

    # Force cleanup of any remaining temporary files
    _temp_manager.cleanup_all()

    # Restore original tempdir
    tempfile.tempdir = original_tempdir

    # Give a short grace period for cleanup
    import time

    time.sleep(0.1)

    # Check for any new temporary files
    after_test = {
        os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if suffix in f
    }

    new_files = after_test - before_test
    if new_files:
        # Clean up any remaining files
        for file in new_files:
            try:
                if os.path.exists(file):
                    os.unlink(file)
            except OSError:
                pass
        pytest.fail(f"Found uncleaned temporary files: {new_files}")


def test_cli_no_temp_files(config_suffix: str) -> None:
    """Test that CLI execution doesn't leave temporary files."""
    runner = CliRunner()

    with runner.isolated_filesystem() as fs:
        # Create a test file
        test_file = Path(fs) / "test.txt"
        test_file.write_text("Test content")

        # Run with explicit output file to avoid default naming
        result = runner.invoke(main, ["-d", ".", "-o", "output" + config_suffix])
        assert result.exit_code == 0

        # Check files in the directory
        files = set(os.listdir(fs))
        temp_files = {
            f for f in files if config_suffix in f and f != "output" + config_suffix
        }
        assert not temp_files, f"Found temporary files: {temp_files}"


def test_cli_cleanup_after_error() -> None:
    """Test that temporary files are cleaned up even after errors."""
    runner = CliRunner()

    with runner.isolated_filesystem() as fs:
        result = runner.invoke(main, ["-d", "nonexistent"])
        assert result.exit_code == 2  # Should fail

        # Check for any temporary files
        temp_files = [f for f in os.listdir(fs) if get_config().output_suffix in f]
        assert not temp_files, f"Found temporary files after error: {temp_files}"


def test_multiple_instances() -> None:
    """Test that multiple FileCombinator instances don't interfere with each other."""
    runner = CliRunner()
    config_suffix = get_config().output_suffix

    with runner.isolated_filesystem() as fs:
        # Create test files
        for i in range(3):
            Path(f"test{i}.txt").write_text(f"Test content {i}")

        # Run multiple instances with explicit output files
        output_files = [f"output{i}{config_suffix}" for i in range(3)]
        results = [
            runner.invoke(main, ["-d", ".", "-o", output_file])
            for output_file in output_files
        ]

        # Check all succeeded
        assert all(r.exit_code == 0 for r in results)

        # Only our explicit output files should remain
        files = set(os.listdir(fs))
        temp_files = {f for f in files if config_suffix in f and f not in output_files}
        assert not temp_files, f"Found temporary files: {temp_files}"


def test_temp_manager_cleanup() -> None:
    """Test that the TempFileManager properly tracks and cleans up files."""
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        temp_name = tf.name
        _temp_manager.register(temp_name)

    # File should exist after creation
    assert os.path.exists(temp_name)

    # Clean up
    _temp_manager.cleanup_all()

    # File should be gone
    assert not os.path.exists(temp_name)
