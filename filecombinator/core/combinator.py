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
from typing import TextIO, cast

from ..processors.content import ContentProcessor
from ..processors.directory import DirectoryProcessor
from .config import get_config
from .exceptions import FileCombinatorError
from .formatting import FormatProcessor
from .models import FileLists, FileStats

logger = logging.getLogger(__name__)


class TempFileManager:
    """Manages temporary files with proper cleanup."""

    def __init__(self) -> None:
        """Initialize the temporary file manager."""
        self._temp_files: set[str] = set()
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
        additional_excludes: set[str] | None = None,
        verbose: bool = False,
        output_file: str | None = None,
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
        self.format_processor = FormatProcessor()
        self.start_time: float | None = None

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

        with tempfile.NamedTemporaryFile(
            mode="w+",
            suffix=get_config().output_suffix,  # Use configured suffix for temp files
            delete=False,
            encoding="utf-8",
        ) as temp_file:
            temp_name = temp_file.name
            _temp_manager.register(temp_name)

            try:
                self.logger.debug("Created temporary file: %s", temp_name)

                output_dir = os.path.dirname(os.path.abspath(output_path))
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)

                # Write AI instructions header
                self.format_processor.write_header(cast(TextIO, temp_file))

                # Generate directory tree
                tree_content = self.directory_processor.generate_tree(directory)
                self.format_processor.format_directory_tree(
                    tree_content, cast(TextIO, temp_file)
                )

                # Process all files
                def process_file(file_path: str) -> None:
                    self.format_processor.format_file_section(
                        file_path, cast(TextIO, temp_file)
                    )
                    self.content_processor.track_file(file_path)

                self.directory_processor.process_directory(directory, process_file)

                temp_file.flush()
                os.fsync(temp_file.fileno())

            except Exception as e:
                self.logger.error("Fatal error during processing: %s", e)
                raise FileCombinatorError(f"Failed to process directory: {e}") from e

            try:
                # Move temporary file to final location
                shutil.move(temp_name, output_path)
                _temp_manager.unregister(temp_name)

                duration = time.time() - self.start_time if self.start_time else 0.0
                self.logger.info("Processing completed in %.2f seconds", duration)
                self._log_statistics(output_path)

            except Exception as e:
                self.logger.error("Error finalizing output: %s", e)
                raise FileCombinatorError(f"Failed to finalize output: {e}") from e

    def _log_statistics(self, output_path: str) -> None:
        """Log processing statistics.

        Args:
            output_path: Path to output file
        """
        stats = self.stats
        self.logger.info("Text files processed: %d", stats.processed)
        self.logger.info("Binary files detected: %d", stats.binary)
        self.logger.info("Image files detected: %d", stats.image)
        self.logger.info("Files skipped due to errors: %d", stats.skipped)
        self.logger.info("Output written to: %s", output_path)

    def _print_excluded_files(self) -> None:
        """Print information about excluded files."""
        file_lists = self.file_lists
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
        """Get current file lists.

        Returns:
            FileLists: Current file lists
        """
        return self.content_processor.file_lists

    @property
    def stats(self) -> FileStats:
        """Get current processing statistics.

        Returns:
            FileStats: Current statistics
        """
        return self.content_processor.stats
