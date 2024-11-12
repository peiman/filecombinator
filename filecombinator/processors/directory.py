# filecombinator/processors/directory.py
"""Directory tree generation and processing for FileCombinator."""

import logging
import os
from pathlib import Path
from typing import Any, Callable, Set

from ..core.exceptions import DirectoryProcessingError

logger = logging.getLogger(__name__)


class DirectoryProcessor:
    """Handles directory traversal and tree generation."""

    def __init__(
        self, exclude_patterns: Set[str], output_file: str | None = None
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

    def generate_tree(self, start_path: str | Path, output_file: Any) -> None:
        """Generate a visual representation of the directory structure.

        Args:
            start_path: Root path to start tree generation from
            output_file: File object to write tree to

        Raises:
            DirectoryProcessingError: If there's an error generating the tree
            ValueError: If output_file is None
        """
        if not os.path.exists(str(start_path)):
            raise DirectoryProcessingError(f"Directory does not exist: {start_path}")

        logger.info("Generating directory tree...")
        try:
            output_file.write(
                "================== DIRECTORY STRUCTURE ==================\n"
            )

            def write_tree(path: str | Path, prefix: str = "") -> None:
                """Recursively write directory tree.

                Args:
                    path: Current path to process
                    prefix: Prefix for current line
                """
                entries = sorted(os.scandir(path), key=lambda e: e.name)
                for i, entry in enumerate(entries):
                    if self.is_excluded(Path(entry.path)):
                        continue

                    is_last = i == len(entries) - 1
                    connector = "└── " if is_last else "├── "
                    output_file.write(f"{prefix}{connector}{entry.name}\n")

                    if entry.is_dir():
                        new_prefix = prefix + ("    " if is_last else "│   ")
                        write_tree(entry.path, new_prefix)

            write_tree(start_path)
            output_file.write(
                "================== END OF DIRECTORY STRUCTURE ==================\n\n"
            )
            logger.info("Directory tree generation completed")
        except (OSError, IOError) as e:
            logger.error("Error generating directory tree: %s", e)
            raise DirectoryProcessingError(
                f"Failed to generate directory tree: {e}"
            ) from e

    def process_directory(
        self,
        directory: str | Path,
        callback: Callable[[str], None],
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
