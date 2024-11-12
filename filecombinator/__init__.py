# filecombinator/__init__.py
"""
FileCombinator - A tool to combine multiple files while preserving directory structure.

This package provides functionality to combine multiple files into a single output file
while maintaining their directory structure and handling different file types.
"""

import importlib.metadata

from .core.combinator import FileCombinator
from .core.exceptions import FileCombinatorError
from .core.models import FileLists, FileStats

try:
    # First, try to get version from installed package
    __version__ = importlib.metadata.version("filecombinator")
except importlib.metadata.PackageNotFoundError:  # pragma: no cover
    try:
        # If not installed, try to get version from setuptools_scm
        from ._version import version as __version__  # noqa
    except ImportError:  # pragma: no cover
        # If running from source without setuptools_scm installed
        __version__ = "0.0.0.dev0"

__author__ = "Peiman Khorramshahi"
__email__ = "peiman@khorramshahi.com"

__all__ = ["FileCombinator", "FileCombinatorError", "FileStats", "FileLists"]
