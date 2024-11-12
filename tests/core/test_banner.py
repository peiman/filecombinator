# tests/core/test_banner.py
"""Test suite for FileCombinator banner functionality."""

import os

from filecombinator.core.banner import get_banner


def test_banner_file_exists() -> None:
    """Test that the banner file exists."""
    banner_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "filecombinator",
        "core",
        "banner.txt",
    )
    assert os.path.exists(banner_path), "Banner file should exist"


def test_get_banner() -> None:
    """Test that get_banner returns a non-empty string."""
    banner = get_banner()
    assert isinstance(banner, str), "Banner should be a string"
    assert len(banner.strip()) > 0, "Banner should not be empty"
