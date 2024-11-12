# filecombinator/core/config.py
"""Configuration management for FileCombinator."""

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set

import yaml

from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Configuration container for FileCombinator."""

    exclude_patterns: Set[str] = field(default_factory=set)
    log_file: str = "logs/file_combinator.log"
    output_suffix: str = "_file_combinator_output.txt"


def get_default_excludes() -> Set[str]:
    """Get the default set of exclude patterns.

    Returns:
        Set[str]: Default exclude patterns
    """
    config = load_config_file()
    return config.exclude_patterns


def load_config_file(config_path: Optional[str] = None) -> Config:
    """Load configuration from YAML file.

    Args:
        config_path: Optional path to config file

    Returns:
        Config: Loaded configuration

    Raises:
        ValueError: If config file is invalid
        ConfigurationError: If config file cannot be loaded
    """
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            try:
                config_data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML format in config file: {e}") from e

            if not isinstance(config_data, dict):
                raise ValueError("Config file must contain a YAML dictionary")

            config = Config()
            config_dict: Dict[str, Any] = config_data

            # Load exclude patterns
            if "exclude_patterns" in config_dict:
                patterns = config_dict["exclude_patterns"]
                if not isinstance(patterns, list):
                    raise ValueError("exclude_patterns must be a list")
                config.exclude_patterns = set(patterns)

            # Load logging configuration
            if "logging" in config_dict:
                logging_config = config_dict["logging"]
                if isinstance(logging_config, dict):
                    config.log_file = logging_config.get(
                        "default_log_file", config.log_file
                    )

            # Load output configuration
            if "output" in config_dict:
                output_config = config_dict["output"]
                if isinstance(output_config, dict):
                    config.output_suffix = output_config.get(
                        "file_suffix", config.output_suffix
                    )

            return config

    except OSError as e:
        logger.error("Failed to load config file: %s", e)
        raise ConfigurationError(f"Could not load config file: {e}") from e


def get_config(additional_excludes: Optional[Set[str]] = None) -> Config:
    """Get configuration with optional additional excludes.

    Args:
        additional_excludes: Additional patterns to exclude

    Returns:
        Config: Combined configuration
    """
    config = load_config_file()

    if additional_excludes:
        config.exclude_patterns.update(additional_excludes)

    return config
