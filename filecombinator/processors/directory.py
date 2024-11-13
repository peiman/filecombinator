# filecombinator/processors/directory.py
"""Directory tree generation and processing for FileCombinator."""

import logging
import os
from pathlib import Path
from typing import Protocol

from ..core.exceptions import DirectoryProcessingError

logger = logging.getLogger(__name__)


class FileCallback(Protocol):
    """Protocol for file callback functions."""

    def __call__(self, file_path: str) -> None:
        """Call the callback function with the file path."""
        ...


class DirectoryProcessor:
    """Handles directory traversal and tree generation."""

    def __init__(
        self, exclude_patterns: set[str], output_file: str | None = None
    ) -> None:
        """Initialize DirectoryProcessor.

        Args:
            exclude_patterns: Set of patterns to exclude from processing
            output_file: Optional path to output file to exclude from processing
        """
        self.exclude_patterns = exclude_patterns
        self.output_file = output_file

    def is_excluded(self, path: Path) -> bool:
        """Check if a path should be excluded.

        Args:
            path: Path to check

        Returns:
            bool: True if path should be excluded, False otherwise
        """
        path_abs = os.path.abspath(path)
        output_abs = os.path.abspath(self.output_file) if self.output_file else None

        if output_abs and path_abs == output_abs:
            logger.debug("Skipping output file: %s", path)
            return True

        file_name = os.path.basename(path)
        if file_name.endswith("_file_combinator_output.txt"):
            logger.debug("Skipping file combinator output file: %s", path)
            return True

        excluded = any(exclude in path.parts for exclude in self.exclude_patterns)
        if excluded:
            logger.debug("Excluded path: %s", path)

        return excluded

    def generate_tree(self, start_path: str | Path) -> str:
        """Generate a string representation of the directory tree.

        Args:
            start_path: Root path to start tree generation from

        Returns:
            str: String representation of the directory tree

        Raises:
            DirectoryProcessingError: If there's an error generating the tree
        """
        if not os.path.exists(str(start_path)):
            raise DirectoryProcessingError(f"Directory does not exist: {start_path}")

        try:
            entries = [
                e for e in os.scandir(start_path) if not self.is_excluded(Path(e.path))
            ]

            if not entries:
                return ""  # Return empty string for empty directories

            lines = []
            root_name = os.path.basename(start_path) or str(start_path)
            lines.append(root_name + "/")

            def add_to_tree(dir_path: Path, prefix: str = "") -> None:
                entries = sorted(os.scandir(dir_path), key=lambda e: e.name)
                entries = [e for e in entries if not self.is_excluded(Path(e.path))]

                for i, entry in enumerate(entries):
                    is_last = i == len(entries) - 1
                    connector = "└── " if is_last else "├── "
                    lines.append(f"{prefix}{connector}{entry.name}")

                    if entry.is_dir():
                        next_prefix = prefix + ("    " if is_last else "│   ")
                        add_to_tree(Path(entry.path), next_prefix)

            add_to_tree(Path(start_path))
            return "\n".join(lines)

        except Exception as e:
            logger.error("Error generating directory tree: %s", e)
            raise DirectoryProcessingError(
                f"Failed to generate directory tree: {e}"
            ) from e

    def process_directory(
        self,
        directory: str | Path,
        callback: FileCallback,
    ) -> None:
        """Process all files in a directory recursively.

        Args:
            directory: Directory to process
            callback: Function to call for each file

        Raises:
            DirectoryProcessingError: If directory can't be processed
        """
        if not os.path.exists(directory):
            raise DirectoryProcessingError(f"Directory does not exist: {directory}")

        try:
            for root, dirs, files in os.walk(directory):
                # Filter out excluded directories
                dirs[:] = [
                    d for d in dirs if not self.is_excluded(Path(os.path.join(root, d)))
                ]

                # Process files
                for file in sorted(files):
                    file_path = os.path.join(root, file)
                    if not self.is_excluded(Path(file_path)):
                        callback(file_path)

        except OSError as e:
            logger.error("Error processing directory %s: %s", directory, e)
            raise DirectoryProcessingError(
                f"Failed to process directory {directory}: {e}"
            ) from e
