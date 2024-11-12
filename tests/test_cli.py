# tests/test_cli.py
"""Test suite for the FileCombinator CLI."""

import os
import tempfile
from typing import Generator

import pytest
from click.testing import CliRunner

from filecombinator.cli import main


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


def test_cli_defaults() -> None:
    """Test CLI with default values."""
    runner = CliRunner(mix_stderr=False)
    with runner.isolated_filesystem():
        # Create a test file
        with open("test.txt", "w") as f:
            f.write("Test content")

        result = runner.invoke(main)
        assert result.exit_code == 0
        output_files = [
            f for f in os.listdir(".") if f.endswith("_file_combinator_output.txt")
        ]
        assert len(output_files) == 1


def test_cli_custom_directory(test_env: tuple[str, str]) -> None:
    """Test CLI with custom input directory."""
    input_dir, _ = test_env
    runner = CliRunner()
    result = runner.invoke(main, ["--directory", input_dir])
    assert result.exit_code == 0
    dirname = os.path.basename(input_dir)
    output_file = f"{dirname}_file_combinator_output.txt"
    assert os.path.exists(output_file)


def test_cli_custom_output(test_env: tuple[str, str]) -> None:
    """Test CLI with custom output file."""
    input_dir, output_dir = test_env
    output_file = os.path.join(output_dir, "custom_output.txt")

    runner = CliRunner()
    result = runner.invoke(main, ["--directory", input_dir, "--output", output_file])
    assert result.exit_code == 0
    assert os.path.exists(output_file)


def test_cli_exclude_patterns(test_env: tuple[str, str]) -> None:
    """Test CLI with exclude patterns."""
    input_dir, _ = test_env

    # Create a directory that should be excluded
    exclude_dir = os.path.join(input_dir, "exclude_me")
    os.makedirs(exclude_dir)
    with open(os.path.join(exclude_dir, "test.txt"), "w") as f:
        f.write("Should be excluded")

    runner = CliRunner()
    result = runner.invoke(main, ["--directory", input_dir, "--exclude", "exclude_me"])
    assert result.exit_code == 0

    # Check output doesn't contain excluded content
    dirname = os.path.basename(input_dir)
    output_file = f"{dirname}_file_combinator_output.txt"
    with open(output_file) as f:
        content = f.read()
        assert "exclude_me" not in content
        assert "Should be excluded" not in content


def test_cli_verbose_output(test_env: tuple[str, str]) -> None:
    """Test CLI with verbose output."""
    input_dir, _ = test_env
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(
        main,
        ["--directory", input_dir, "--verbose", "--no-style"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    all_output = result.stdout + (result.stderr or "")
    assert "DEBUG:" in all_output


def test_cli_error_handling() -> None:
    """Test CLI error handling with nonexistent directory."""
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(
        main,
        ["--directory", "nonexistent"],
        catch_exceptions=False,
    )
    assert result.exit_code == 2  # System exit for fatal errors
    all_output = result.stdout + (result.stderr or "")
    assert "Error" in all_output


def test_cli_help() -> None:
    """Test CLI help output."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "Options:" in result.output


def test_cli_version() -> None:
    """Test CLI version output."""
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output.lower()


def test_cli_style_output(test_env: tuple[str, str]) -> None:
    """Test CLI styled output with Rich."""
    input_dir, _ = test_env
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--directory", input_dir, "--style"],
        color=True,
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    # For colored output, check for typical banner text
    assert (
        "     _____ _ _         ____                _     _             _"
        in result.output
    )  # Banner content
    # And check that processing completed message is present
    assert "Processing completed" in result.output
