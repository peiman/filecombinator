# filecombinator/core/combinator.py
"""Core FileCombinator class implementation."""

import logging
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Optional, Set

from ..processors.content import ContentProcessor
from ..processors.directory import DirectoryProcessor
from .exceptions import FileCombinatorError
from .logging import setup_logging
from .models import FileLists, FileStats

logger = logging.getLogger(__name__)


class FileCombinator:
    """Combines multiple files into a single output file while preserving structure."""

    # Default exclusion patterns
    DEFAULT_EXCLUDES: Set[str] = {
        "__pycache__",
        ".venv",
        ".git",
        "node_modules",
        ".DS_Store",
        ".pytest_cache",
        ".vscode",
        "logs",
        ".mypy_cache",
        ".cache",
        ".pythonlibs",
        ".local",
        "gitdiff.txt",
    }

    def __init__(
        self,
        additional_excludes: Optional[Set[str]] = None,
        verbose: bool = False,
        output_file: Optional[str] = None,
    ) -> None:
        """Initialize FileCombinator.

        Args:
            additional_excludes: Additional patterns to exclude
            verbose: Enable verbose logging
            output_file: Path to output file
        """
        self.exclude_patterns = self.DEFAULT_EXCLUDES.copy()
        if additional_excludes:
            self.exclude_patterns.update(additional_excludes)
        self.verbose = verbose
        self.output_file = output_file
        self.logger = logging.getLogger("FileCombinator")

        # Initialize processors
        self.directory_processor = DirectoryProcessor(
            self.exclude_patterns, self.output_file
        )
        self.content_processor = ContentProcessor()
        self.start_time: Optional[float] = None

    @staticmethod
    def setup_logging(
        log_file: Optional[str] = None, verbose: bool = False
    ) -> logging.Logger:
        """Set up logging configuration."""
        return setup_logging(log_file, verbose)

    @staticmethod
    def display_banner() -> None:
        """Display the application banner."""
        from .banner import get_banner

        print(get_banner())

    def process_directory(self, directory: str | Path, output_path: str) -> None:
        """Process a directory and combine its contents.

        Args:
            directory: Directory to process
            output_path: Path to output file

        Raises:
            FileCombinatorError: If there's an error processing the directory
        """
        self.start_time = time.time()
        self.logger.info("Starting directory processing: %s", directory)

        # Update output file for proper exclusion
        self.output_file = output_path
        self.directory_processor.output_file = output_path

        temp_fd = None
        temp_name = None

        try:
            # Create a temporary file securely
            temp_fd, temp_name = tempfile.mkstemp(suffix=".txt")
            os.close(temp_fd)  # Close the file descriptor

            # Ensure output directory exists
            output_dir = os.path.dirname(os.path.abspath(output_path))
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            # Open the temporary file for writing
            with open(temp_name, "w", encoding="utf-8") as temp_file:
                self.logger.debug("Created temporary file: %s", temp_name)

                # Generate directory tree
                self.directory_processor.generate_tree(directory, temp_file)

                # Process all files
                self.directory_processor.process_directory(
                    directory,
                    lambda file_path: self.content_processor.process_file(
                        file_path, temp_file
                    ),
                )

            # Move temporary file to final location
            shutil.move(temp_name, output_path)

            # Print processing summary
            duration = time.time() - self.start_time
            self.logger.info("Processing completed in %.2f seconds", duration)
            self._log_statistics(output_path)

            # Show excluded files
            self._print_excluded_files()

        except Exception as e:
            self.logger.error("Fatal error during processing: %s", e)
            raise FileCombinatorError(f"Failed to process directory: {e}") from e
        finally:
            # Clean up temporary file if it still exists
            if temp_name and os.path.exists(temp_name):
                try:
                    os.unlink(temp_name)
                except OSError:
                    pass  # Ignore cleanup errors

    def _log_statistics(self, output_path: str) -> None:
        """Log processing statistics.

        Args:
            output_path: Path to output file
        """
        stats = self.content_processor.stats
        self.logger.info("Text files processed: %d", stats.processed)
        self.logger.info("Binary files detected: %d", stats.binary)
        self.logger.info("Image files detected: %d", stats.image)
        self.logger.info("Files skipped due to errors: %d", stats.skipped)
        self.logger.info("Output written to: %s", output_path)

    def _print_excluded_files(self) -> None:
        """Print information about excluded files."""
        file_lists = self.content_processor.file_lists
        for file_type, files in [
            ("Binary", file_lists.binary),
            ("Image", file_lists.image),
        ]:
            if files:
                print(f"\n{file_type} files detected and excluded:")
                for file_name in files:
                    print(f"  {file_name}")

    @property
    def file_lists(self) -> FileLists:
        """Get current file lists."""
        return self.content_processor.file_lists

    @property
    def stats(self) -> FileStats:
        """Get current processing statistics."""
        return self.content_processor.stats
