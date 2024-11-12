# filecombinator/core/banner.py
"""Banner loading functionality for FileCombinator."""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)
_banner: Optional[str] = None


def get_banner() -> str:
    """Get the application banner from the banner file.

    Returns:
        str: The banner string

    Note:
        The banner is cached after first load for efficiency.
    """
    global _banner

    if _banner is not None:
        return _banner

    banner_path = os.path.join(os.path.dirname(__file__), "banner.txt")

    try:
        with open(banner_path, "r", encoding="utf-8") as f:
            _banner = f.read()
        return _banner
    except (IOError, OSError) as e:
        logger.error("Failed to load banner: %s", e)
        return ""  # Return empty string as fallback
