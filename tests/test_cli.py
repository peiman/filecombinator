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
    runner = CliRunner()
    with runner.isolated_filesystem():  # Removed unused variable 'fs'
        # Create a test file
        os.makedirs("testdir")
        with open(os.path.join("testdir", "test.txt"), "w") as f:
            f.write("Test content")

        # Test with default output filename
        result = runner.invoke(main, ["-d", "testdir"])
        assert result.exit_code == 0

        # Check for default output file
        expected_output = "testdir_file_combinator_output.txt"
        assert os.path.exists(expected_output)

        # Verify content
        with open(expected_output, "r") as f:
            content = f.read()
            assert "test.txt" in content
            assert "Test content" in content


def test_cli_default_output_current_dir() -> None:
    """Test CLI with default output filename in current directory."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test file in current directory
        with open("test.txt", "w") as f:
            f.write("Test content")

        # Run with current directory
        result = runner.invoke(main)
        assert result.exit_code == 0

        # Get current directory name
        current_dir = os.path.basename(os.path.abspath("."))
        expected_output = f"{current_dir}_file_combinator_output.txt"
        assert os.path.exists(expected_output)

        # Verify content
        with open(expected_output, "r") as f:
            content = f.read()
            assert "test.txt" in content
            assert "Test content" in content


def test_cli_custom_directory(test_env: tuple[str, str]) -> None:
    """Test CLI with custom input directory."""
    input_dir, output_dir = test_env
    runner = CliRunner()

    # Use explicit output file in output directory
    output_file = os.path.join(output_dir, "output.txt")
    result = runner.invoke(main, ["--directory", input_dir, "--output", output_file])

    assert result.exit_code == 0
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
    input_dir, output_dir = test_env

    # Create a directory that should be excluded
    exclude_dir = os.path.join(input_dir, "exclude_me")
    os.makedirs(exclude_dir)
    with open(os.path.join(exclude_dir, "test.txt"), "w") as f:
        f.write("Should be excluded")

    runner = CliRunner()
    output_file = os.path.join(output_dir, "output.txt")
    result = runner.invoke(
        main,
        ["--directory", input_dir, "--exclude", "exclude_me", "--output", output_file],
    )
    assert result.exit_code == 0

    # Check output doesn't contain excluded content
    with open(output_file) as f:
        content = f.read()
        assert "exclude_me" not in content
        assert "Should be excluded" not in content


def test_cli_multiple_excludes(test_env: tuple[str, str]) -> None:
    """Test CLI with multiple exclude patterns."""
    input_dir, output_dir = test_env

    # Create directories that should be excluded
    for exclude_dir in ["exclude1", "exclude2"]:
        full_path = os.path.join(input_dir, exclude_dir)
        os.makedirs(full_path)
        with open(os.path.join(full_path, "test.txt"), "w") as f:
            f.write(f"Content in {exclude_dir}")

    output_file = os.path.join(output_dir, "output.txt")
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--directory",
            input_dir,
            "--exclude",
            "exclude1",
            "--exclude",
            "exclude2",
            "--output",
            output_file,
        ],
    )
    assert result.exit_code == 0

    with open(output_file) as f:
        content = f.read()
        assert "exclude1" not in content
        assert "exclude2" not in content


def test_cli_verbose_output(test_env: tuple[str, str]) -> None:
    """Test CLI with verbose output."""
    input_dir, output_dir = test_env
    output_file = os.path.join(output_dir, "output.txt")

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(
        main,
        [
            "--directory",
            input_dir,
            "--verbose",
            "--no-style",
            "--output",
            output_file,
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    print("\nDEBUG OUTPUT:")
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    # Let's check both stdout and stderr individually
    debug_messages = [
        "Created temporary file:",
        "Starting directory processing:",
        "Processing completed in",
        "Text files processed:",
    ]

    combined_output = (result.stdout or "") + (result.stderr or "")

    for msg in debug_messages:
        if msg in combined_output:
            print(f"Found message: {msg}")

    found_any = any(msg in combined_output for msg in debug_messages)
    assert found_any, (
        f"No expected log messages found in output. "
        f"Looking for any of: {debug_messages}. "
        f"Got stdout: {result.stdout}\n"
        f"Got stderr: {result.stderr}"
    )


def test_cli_error_handling() -> None:
    """Test CLI error handling with nonexistent directory."""
    runner = CliRunner(mix_stderr=False)
    with runner.isolated_filesystem() as fs:
        output_file = os.path.join(fs, "output.txt")
        result = runner.invoke(
            main,
            ["--directory", "nonexistent", "--output", output_file],
            catch_exceptions=False,
        )
        assert result.exit_code == 2  # System exit for fatal errors
        # Just verify it contains error indication
        assert any(
            error_text in (result.stderr or "")
            for error_text in ["Error", "does not exist", "nonexistent"]
        )


def test_cli_help() -> None:
    """Test CLI help output."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    # Just verify essential help content
    assert "Usage:" in result.output
    assert "-d, --directory" in result.output
    assert "-o, --output" in result.output


def test_cli_version() -> None:
    """Test CLI version output."""
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output.lower()
