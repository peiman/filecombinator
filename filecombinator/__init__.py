# filecombinator/__init__.py
"""
FileCombinator - A tool to combine multiple files while preserving directory structure.

This package provides functionality to combine multiple files into a single output file
while maintaining their directory structure and handling different file types.
"""

from .core.combinator import FileCombinator
from .core.exceptions import FileCombinatorError
from .core.models import FileLists, FileStats

__version__ = "0.1.0"
__author__ = "Peiman Khorramshahi"
__email__ = "peiman@khorramshahi.com"

__all__ = ["FileCombinator", "FileCombinatorError", "FileStats", "FileLists"]
