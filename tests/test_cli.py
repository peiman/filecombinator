# tests/test_cli.py
"""Test suite for the FileCombinator CLI."""

import os
import tempfile
from typing import Generator

import pytest

from filecombinator.cli import main, parse_args


@pytest.fixture
def test_env() -> Generator[tuple[str, str], None, None]:
    """Create a test environment with input and output directories.

    Returns:
        Tuple of (input directory path, output directory path)
    """
    with (
        tempfile.TemporaryDirectory() as input_dir,
        tempfile.TemporaryDirectory() as output_dir,
    ):
        # Create some test files
        with open(os.path.join(input_dir, "test.txt"), "w") as f:
            f.write("Test content")
        with open(os.path.join(input_dir, "test.bin"), "wb") as f:
            f.write(b"\x00\x01")

        yield input_dir, output_dir


def test_parse_args_defaults() -> None:
    """Test argument parsing with default values."""
    args = parse_args([])
    assert args.directory == "."
    assert args.output is None
    assert args.exclude is None
    assert not args.verbose
    assert args.log_file == "logs/file_combinator.log"


def test_parse_args_custom() -> None:
    """Test argument parsing with custom values."""
    args = parse_args(
        [
            "-d",
            "/test/dir",
            "-o",
            "output.txt",
            "-e",
            "exclude1",
            "exclude2",
            "-v",
            "--log-file",
            "custom.log",
        ]
    )
    assert args.directory == "/test/dir"
    assert args.output == "output.txt"
    assert args.exclude == ["exclude1", "exclude2"]
    assert args.verbose
    assert args.log_file == "custom.log"


def test_main_basic_processing(test_env: tuple[str, str]) -> None:
    """Test basic file processing through CLI."""
    input_dir, _ = test_env
    output_file = os.path.join(input_dir, "output.txt")

    exit_code = main(["-d", input_dir, "-o", output_file])
    assert exit_code == 0
    assert os.path.exists(output_file)

    with open(output_file, "r") as f:
        content = f.read()
        assert "DIRECTORY STRUCTURE" in content
        assert "test.txt" in content
        assert "Test content" in content
        assert "BINARY FILE (CONTENT EXCLUDED)" in content


def test_main_nonexistent_directory() -> None:
    """Test CLI with nonexistent directory."""
    exit_code = main(["-d", "nonexistent", "-o", "output.txt"])
    assert exit_code == 1


def test_main_with_excludes(test_env: tuple[str, str]) -> None:
    """Test CLI with exclude patterns."""
    input_dir, _ = test_env
    output_file = os.path.join(input_dir, "output.txt")

    # Create a file that should be excluded
    os.makedirs(os.path.join(input_dir, "exclude_me"))
    with open(os.path.join(input_dir, "exclude_me", "test.txt"), "w") as f:
        f.write("Should be excluded")

    exit_code = main(["-d", input_dir, "-o", output_file, "-e", "exclude_me"])
    assert exit_code == 0

    with open(output_file, "r") as f:
        content = f.read()
        assert "exclude_me" not in content
        assert "Should be excluded" not in content


def test_main_verbose_output(
    test_env: tuple[str, str], caplog: pytest.LogCaptureFixture
) -> None:
    """Test CLI with verbose output."""
    input_dir, _ = test_env
    output_file = os.path.join(input_dir, "output.txt")

    exit_code = main(["-d", input_dir, "-o", output_file, "-v"])
    assert exit_code == 0
    assert any(record.levelname == "DEBUG" for record in caplog.records)


def test_main_with_logging(test_env: tuple[str, str]) -> None:
    """Test CLI with log file output."""
    input_dir, output_dir = test_env
    output_file = os.path.join(output_dir, "output.txt")
    log_file = os.path.join(output_dir, "test.log")

    exit_code = main(["-d", input_dir, "-o", output_file, "--log-file", log_file])
    assert exit_code == 0
    assert os.path.exists(log_file)


def test_main_keyboard_interrupt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test CLI handling of keyboard interrupt."""

    def mock_process(*args: str, **kwargs: str) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(
        "filecombinator.core.combinator.FileCombinator.process_directory", mock_process
    )
    exit_code = main(["-d", ".", "-o", "output.txt"])
    assert exit_code == 1


def test_main_unexpected_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test CLI handling of unexpected errors."""

    def mock_process(*args: str, **kwargs: str) -> None:
        raise RuntimeError("Unexpected error")

    monkeypatch.setattr(
        "filecombinator.core.combinator.FileCombinator.process_directory", mock_process
    )
    exit_code = main(["-d", ".", "-o", "output.txt"])
    assert exit_code == 1
