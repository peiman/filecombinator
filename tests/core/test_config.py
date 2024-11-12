# tests/core/test_config.py
"""Test suite for FileCombinator configuration."""

import os
from pathlib import Path
from typing import Set

import pytest

from filecombinator.core.config import (
    Config,
    get_config,
    get_default_excludes,
    load_config_file,
)


def test_default_excludes() -> None:
    """Test that default excludes are loaded correctly."""
    excludes = get_default_excludes()
    assert isinstance(excludes, set)
    assert "__pycache__" in excludes
    assert ".git" in excludes
    assert ".venv" in excludes


def test_config_file_exists() -> None:
    """Test that the default config file exists."""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "filecombinator",
        "core",
        "config.yaml",
    )
    assert os.path.exists(config_path), "Config file should exist"


def test_load_config_file() -> None:
    """Test loading configuration from file."""
    config = load_config_file()
    assert isinstance(config, Config)
    assert isinstance(config.exclude_patterns, set)
    assert len(config.exclude_patterns) > 0


def test_get_config() -> None:
    """Test getting configuration with custom excludes."""
    custom_excludes: Set[str] = {"custom1", "custom2"}
    config = get_config(additional_excludes=custom_excludes)

    # Should include both default and custom excludes
    assert "custom1" in config.exclude_patterns
    assert "custom2" in config.exclude_patterns
    assert "__pycache__" in config.exclude_patterns


def test_get_config_without_custom_excludes() -> None:
    """Test getting configuration without custom excludes."""
    config = get_config()
    assert isinstance(config.exclude_patterns, set)
    assert "__pycache__" in config.exclude_patterns


def test_invalid_config_file(tmp_path: Path) -> None:
    """Test handling of invalid config file."""
    test_config = tmp_path / "invalid_config.yaml"
    test_config.write_text("invalid: yaml: content}]")

    with pytest.raises(ValueError):
        load_config_file(str(test_config))
