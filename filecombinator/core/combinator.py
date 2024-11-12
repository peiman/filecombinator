# filecombinator/core/combinator.py
"""Core FileCombinator class implementation."""

import atexit
import contextlib
import logging
import os
import shutil
import tempfile
import time
import weakref
from pathlib import Path
from typing import Optional, Set

from ..processors.content import ContentProcessor
from ..processors.directory import DirectoryProcessor
from .config import get_config
from .exceptions import FileCombinatorError
from .models import FileLists, FileStats

logger = logging.getLogger(__name__)


class TempFileManager:
    """Manages temporary files with proper cleanup."""

    def __init__(self) -> None:
        """Initialize the temporary file manager."""
        self._temp_files: Set[str] = set()
        # Register cleanup on garbage collection
        weakref.finalize(self, self.cleanup_all)

    def register(self, filepath: str) -> None:
        """Register a temporary file for cleanup.

        Args:
            filepath: Path to the temporary file
        """
        self._temp_files.add(filepath)

    def unregister(self, filepath: str) -> None:
        """Unregister a temporary file from cleanup.

        Args:
            filepath: Path to the temporary file
        """
        self._temp_files.discard(filepath)

    def cleanup_all(self) -> None:
        """Clean up all registered temporary files."""
        for filepath in list(self._temp_files):
            with contextlib.suppress(OSError):
                if os.path.exists(filepath):
                    os.unlink(filepath)
                    self._temp_files.discard(filepath)
                    logger.debug("Cleaned up temporary file: %s", filepath)


# Global temporary file manager
_temp_manager = TempFileManager()

# Register cleanup on program exit
atexit.register(_temp_manager.cleanup_all)


class FileCombinator:
    """Combines multiple files into a single output file while preserving structure."""

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
        config = get_config(additional_excludes)
        self.exclude_patterns = config.exclude_patterns
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

        # Use a with block for better cleanup handling
        with tempfile.NamedTemporaryFile(
            mode="w+",
            suffix="_file_combinator_output.txt",
            delete=False,
            encoding="utf-8",
        ) as temp_file:
            temp_name = temp_file.name
            _temp_manager.register(temp_name)

            try:
                self.logger.debug("Created temporary file: %s", temp_name)

                # Ensure output directory exists
                output_dir = os.path.dirname(os.path.abspath(output_path))
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)

                # Generate directory tree
                self.directory_processor.generate_tree(directory, temp_file)

                # Process all files
                self.directory_processor.process_directory(
                    directory,
                    lambda file_path: self.content_processor.process_file(
                        file_path, temp_file
                    ),
                )

                # Ensure all content is written
                temp_file.flush()
                os.fsync(temp_file.fileno())

            except Exception as e:
                self.logger.error("Fatal error during processing: %s", e)
                raise FileCombinatorError(f"Failed to process directory: {e}") from e

        try:
            # Move temporary file to final location
            shutil.move(temp_name, output_path)
            _temp_manager.unregister(temp_name)

            # Print processing summary
            duration = time.time() - self.start_time
            self.logger.info("Processing completed in %.2f seconds", duration)
            self._log_statistics(output_path)

            # Show excluded files
            self._print_excluded_files()

        except Exception as e:
            self.logger.error("Error finalizing output: %s", e)
            raise FileCombinatorError(f"Failed to finalize output: {e}") from e

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
