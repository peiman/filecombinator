# filecombinator/core/logging.py
"""Logging configuration for FileCombinator."""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logging(
    log_file: Optional[str] = None, verbose: bool = False
) -> logging.Logger:
    """Set up logging configuration.

    Args:
        log_file: Optional path to log file
        verbose: Whether to enable verbose logging

    Returns:
        logging.Logger: Configured logger instance
    """
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger("FileCombinator")
    logger.setLevel(logging.DEBUG)
    logger.handlers = []  # Clear any existing handlers

    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    simple_formatter = logging.Formatter("%(levelname)s: %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(simple_formatter)
    console_handler.setLevel(logging.INFO if not verbose else logging.DEBUG)
    logger.addHandler(console_handler)

    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(detailed_formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

    return logger
