# filecombinator/core/models.py
"""Data models for the FileCombinator package."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class FileStats:
    """Track file processing statistics and counters."""

    processed: int = 0
    skipped: int = 0
    binary: int = 0
    image: int = 0


@dataclass
class FileLists:
    """Container for processed file lists."""

    text: List[str] = field(default_factory=list)
    binary: List[str] = field(default_factory=list)
    image: List[str] = field(default_factory=list)
