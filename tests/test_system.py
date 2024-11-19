"""System tests to verify end-to-end functionality."""

import os
import subprocess
from pathlib import Path

import pytest

from filecombinator.core.config import get_config


@pytest.fixture
def test_dir(tmp_path: Path) -> Path:
    """Set up test directory with files."""
    # Create base directory
    proj_dir = tmp_path / "test_proj"
    proj_dir.mkdir()

    # Create source files
    src_dir = proj_dir / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("def main():\n    print('Hello')\n")
    (src_dir / "utils.py").write_text("def util():\n    return True\n")

    # Create excluded directory
    venv_dir = proj_dir / ".venv"
    venv_dir.mkdir()
    (venv_dir / "lib").write_text("exclude me")

    # Create binary file
    with open(proj_dir / "test.bin", "wb") as f:
        f.write(b"\x00\x01\x02\x03")

    return proj_dir


@pytest.mark.end_to_end
def test_cli(
    test_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """End-to-end test of CLI functionality."""
    # Get CLI path
    venv_bin = os.path.join(os.environ.get("VIRTUAL_ENV", ""), "bin")
    if not os.path.exists(venv_bin):
        pytest.skip("Test requires virtual environment")

    cli_path = os.path.join(venv_bin, "filecombinator")
    if not os.path.exists(cli_path):
        pytest.skip("CLI not installed")

    # Save original dir
    orig_dir = os.getcwd()
    try:
        # Change to test directory
        os.chdir(test_dir)

        # Run CLI without coverage to avoid data issues
        env = os.environ.copy()
        env.pop("COVERAGE_FILE", None)
        env.pop("COVERAGE_PROCESS_START", None)

        # Execute CLI
        result = subprocess.run(
            [cli_path], env=env, capture_output=True, text=True, check=False
        )

        print("\nDEBUG: CLI Output:")
        print(result.stdout)
        print("\nDEBUG: CLI Errors:")
        print(result.stderr)

        # Check execution
        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        # Check output file
        output_file = f"test_proj{get_config().output_suffix}"
        assert os.path.exists(output_file)

        # Check content
        content = Path(output_file).read_text()

        # Structure checks
        assert "Directory Structure" in content
        assert "test_proj/" in content
        assert "src" in content
        assert ".venv" not in content

        # File checks
        assert "def main():" in content
        assert "def util():" in content
        assert "**Type**: Binary" in content
        assert "**Type**: Text" in content
        assert "*Content excluded: Binary file*" in content

    finally:
        os.chdir(orig_dir)


@pytest.mark.end_to_end
def test_cli_exclude(test_dir: Path) -> None:
    """Test CLI exclude functionality."""
    venv_bin = os.path.join(os.environ.get("VIRTUAL_ENV", ""), "bin")
    if not os.path.exists(venv_bin):
        pytest.skip("Test requires virtual environment")

    cli_path = os.path.join(venv_bin, "filecombinator")
    if not os.path.exists(cli_path):
        pytest.skip("CLI not installed")

    # Execute from test directory
    orig_dir = os.getcwd()
    try:
        os.chdir(test_dir)
        env = os.environ.copy()
        env.pop("COVERAGE_FILE", None)
        env.pop("COVERAGE_PROCESS_START", None)

        result = subprocess.run(
            [cli_path, "-e", "src"],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0

        output_file = f"test_proj{get_config().output_suffix}"
        content = Path(output_file).read_text()

        assert "src/main.py" not in content
        assert "test.bin" in content
        assert ".venv" not in content

    finally:
        os.chdir(orig_dir)


@pytest.mark.end_to_end
def test_cli_help() -> None:
    """Test CLI help output."""
    venv_bin = os.path.join(os.environ.get("VIRTUAL_ENV", ""), "bin")
    if not os.path.exists(venv_bin):
        pytest.skip("Test requires virtual environment")

    cli_path = os.path.join(venv_bin, "filecombinator")
    if not os.path.exists(cli_path):
        pytest.skip("CLI not installed")

    # Run help without coverage
    env = os.environ.copy()
    env.pop("COVERAGE_FILE", None)
    env.pop("COVERAGE_PROCESS_START", None)

    result = subprocess.run(
        [cli_path, "--help"], env=env, capture_output=True, text=True, check=False
    )

    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert "-d, --directory" in result.stdout
    assert "-e, --exclude" in result.stdout
