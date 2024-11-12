# tests/test_version.py
"""Test suite for version management."""

import re
from typing import Optional

from filecombinator import __version__


def test_version_format() -> None:
    """Test that version string follows semantic versioning."""
    # setuptools_scm can add additional info after the version number
    # e.g., "0.2.0.dev1+g1234567" or "0.2.0+dirty"
    version_pattern = re.compile(r"^\d+\.\d+\.\d+")
    assert version_pattern.match(
        __version__
    ), "Version should start with semantic versioning"


def test_version_components() -> None:
    """Test that version components are valid integers."""
    # Get the main version numbers before any additional setuptools_scm info
    match: Optional[re.Match[str]] = re.match(r"^\d+\.\d+\.\d+", __version__)
    assert match is not None, "Version should match semantic versioning pattern"
    version_base = match.group(0)
    major, minor, patch = map(int, version_base.split("."))
    assert all(
        x >= 0 for x in [major, minor, patch]
    ), "Version components should be >= 0"


def test_version_development() -> None:
    """Test that version indicates development state correctly."""
    # In development, version should end with .dev0 or similar
    assert __version__ in ["0.0.0.dev0"] or not __version__.endswith(
        ".dev0"
    ), "Version should either be development or release version"
