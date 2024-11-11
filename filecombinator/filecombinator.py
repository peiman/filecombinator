# filecombinator/filecombinator.py
"""
FileCombinator - A tool for combining files while preserving directory structure.

This module provides functionality to combine multiple files into a
single output file while maintaining their directory structure and
handling different file types appropriately.
"""
from __future__ import annotations

import argparse
import dataclasses
import logging
import os
import shutil
import sys
import tempfile
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from types import TracebackType
from typing import Any, Dict, List, Optional, Set, Type


@dataclasses.dataclass
class FileStats:
    """Track file processing statistics and counters."""

    processed: int = 0
    skipped: int = 0
    binary: int = 0
    image: int = 0


@dataclasses.dataclass
class FileLists:
    """Container for processed file lists."""

    text: List[str] = dataclasses.field(default_factory=list)
    binary: List[str] = dataclasses.field(default_factory=list)
    image: List[str] = dataclasses.field(default_factory=list)


class FileCombinatorError(Exception):
    """Base exception for FileCombinator errors."""


# Try to import magic, but don't fail if it's not available
try:
    import magic

    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False


class SafeOpen:
    """Context manager for safely opening files with proper resource management."""

    def __init__(
        self,
        file_path: str | Path,
        mode: str = "r",
        encoding: str = "utf-8",
        **kwargs: Any,
    ) -> None:
        """Initialize the context manager with proper encoding by default."""
        self.file_path = file_path
        self.mode = mode
        self.kwargs = kwargs
        if "b" not in mode:
            self.kwargs["encoding"] = encoding
        self.file_obj: Any = None

    def __enter__(self) -> Any:
        """Open and return the file object with proper encoding."""
        self.file_obj = open(self.file_path, self.mode, **self.kwargs)
        return self.file_obj

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Close the file object."""
        if self.file_obj is not None:
            self.file_obj.close()


class FileCombinator:
    """
    A class that combines multiple files into a single output file.

    This is done while preserving directory structure and handling
    different file types appropriately.
    """

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

    # Image file extensions
    IMAGE_EXTENSIONS: Set[str] = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".tiff",
        ".webp",
        ".svg",
        ".ico",
    }

    # Known binary file extensions
    BINARY_EXTENSIONS: Set[str] = {
        ".pyc",
        ".pyo",
        ".pyd",
        ".so",
        ".dll",
        ".dylib",
        ".exe",
        ".bin",
        ".coverage",
        ".pkl",
        ".pdb",
        ".o",
        ".obj",
        ".db",
        ".sqlite",
        ".sqlite3",
        ".jar",
        ".war",
        ".class",
        ".pdf",
    }

    def __init__(
        self,
        additional_excludes: Optional[Set[str]] = None,
        verbose: bool = False,
        output_file: Optional[str] = None,
    ) -> None:
        """Initialize FileCombinator."""
        # Configuration
        self.exclude_patterns = self.DEFAULT_EXCLUDES.copy()
        if additional_excludes:
            self.exclude_patterns.update(additional_excludes)
        self.verbose = verbose
        self.output_file = output_file
        self.logger = logging.getLogger("FileCombinator")

        # Statistics and file tracking
        self._stats = FileStats()
        self._files = FileLists()
        self.start_time: Optional[float] = None

        # File type detection
        self.mime: Optional[Any] = None
        if MAGIC_AVAILABLE:
            try:
                self.mime = magic.Magic(mime=True)
                self.logger.debug("Magic library initialized successfully")
            except IOError as e:
                self.logger.debug("Could not initialize magic library: %s", e)

    @staticmethod
    def setup_logging(
        log_file: Optional[str] = None, verbose: bool = False
    ) -> logging.Logger:
        """Set up logging configuration."""
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

    @staticmethod
    def display_banner() -> None:
        """Display the application banner."""
        banner = r"""
     _____ _ _         ____                _     _             _
    |  ___(_) | ___   / ___|___  _ __ ___ | |__ (_)_ __   __ _| |_ ___  _ __
    | |_  | | |/ _ \ | |   / _ \| '_ ` _ \| '_ \| | '_ \ / _` | __/ _ \| '__|
    |  _| | | |  __/ | |__| (_) | | | | | | |_) | | | | | (_| | || (_) | |
    |_|   |_|_|\___|  \____\___/|_| |_| |_|_.__/|_|_| |_|\__,_|\__\___/|_|
    """
        print(banner)

    # Properties for statistics
    @property
    def processed_files(self) -> int:
        """Get count of processed files."""
        return self._stats.processed

    @property
    def skipped_files(self) -> int:
        """Get count of skipped files."""
        return self._stats.skipped

    @property
    def binary_files(self) -> int:
        """Get count of binary files."""
        return self._stats.binary

    @property
    def image_files(self) -> int:
        """Get count of image files."""
        return self._stats.image

    # Properties for file lists
    @property
    def text_files(self) -> List[str]:
        """Get list of processed text files."""
        return self._files.text

    @property
    def binary_file_names(self) -> List[str]:
        """Get list of binary file names."""
        return self._files.binary

    @property
    def image_file_names(self) -> List[str]:
        """Get list of image file names."""
        return self._files.image

    def is_excluded(self, path: Path) -> bool:
        """Check if a path should be excluded."""
        path_abs = os.path.abspath(path)
        output_abs = os.path.abspath(self.output_file) if self.output_file else None

        if output_abs and path_abs == output_abs:
            self.logger.debug("Skipping output file: %s", path)
            return True

        file_name = os.path.basename(path)
        if file_name.endswith("_file_combinator_output.txt"):
            self.logger.debug("Skipping file combinator output file: %s", path)
            return True

        excluded = any(exclude in path.parts for exclude in self.exclude_patterns)
        if excluded:
            self.logger.debug("Excluded path: %s", path)

        return excluded

    def is_image_file(self, file_path: str | Path) -> bool:
        """Check if a file is an image."""
        if self.mime:
            try:
                mime_type = self.mime.from_file(str(file_path))
                if mime_type.startswith("image/"):
                    return True
            except IOError as e:
                self.logger.debug("Error checking mime type: %s", e)

        return Path(file_path).suffix.lower() in self.IMAGE_EXTENSIONS

    def is_binary_file(self, file_path: str | Path) -> bool:
        """Detect if a file is binary."""
        if Path(file_path).suffix.lower() in self.BINARY_EXTENSIONS:
            return True

        if self.mime:
            try:
                mime_type = self.mime.from_file(str(file_path))
                return not mime_type.startswith(
                    ("text/", "application/json", "application/xml")
                )
            except IOError as e:
                self.logger.debug("Error checking mime type: %s", e)

        try:
            with SafeOpen(file_path, "rb") as f:
                chunk = f.read(4096)
                textchars = bytes(
                    {7, 8, 9, 10, 12, 13, 27}
                    | set(range(0x20, 0x7F))
                    | set(range(0x80, 0xFF))
                )
                return bool(chunk.translate(None, textchars))
        except IOError as e:
            self.logger.debug("Error reading file: %s", e)
            return True

    def get_file_info(self, file_path: str | Path) -> Dict[str, Any]:
        """Get file information including size, modification time, and type."""
        try:
            stat = os.stat(file_path)
            file_type = "Text"
            if self.is_binary_file(file_path):
                file_type = "Binary"
            elif self.is_image_file(file_path):
                file_type = "Image"

            return {
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "type": file_type,
            }
        except OSError as e:
            self.logger.error("Error getting file info for %s: %s", file_path, e)
            raise FileCombinatorError(f"Failed to get file info: {e}") from e

    def process_file(self, file_path: str | Path, output_file: Any) -> None:
        """Process a single file."""
        try:
            relative_path = os.path.relpath(file_path)
            self.logger.debug("Processing file: %s", relative_path)

            file_info = self.get_file_info(file_path)
            separator = "=" * 18

            output_file.write(f"\n{separator} FILE SEPARATOR {separator}\n")
            output_file.write(f"FILEPATH: {relative_path}\n")
            output_file.write(
                f"Metadata: Type: {file_info['type']}, "
                f"Size: {file_info['size']} bytes, "
                f"Last Modified: {file_info['modified']}\n"
            )

            if file_info["type"] == "Image":
                output_file.write(
                    f"{separator} IMAGE FILE (CONTENT EXCLUDED) {separator}\n"
                )
                self._increment_stat("image")
                self._add_file("image", relative_path)
                self.logger.info("Skipping content of image file: %s", relative_path)
            elif file_info["type"] == "Binary":
                output_file.write(
                    f"{separator} BINARY FILE (CONTENT EXCLUDED) {separator}\n"
                )
                self._increment_stat("binary")
                self._add_file("binary", relative_path)
                self.logger.info("Skipping content of binary file: %s", relative_path)
            else:
                output_file.write(f"{separator} START OF FILE {separator}\n")
                try:
                    with SafeOpen(file_path, "r", encoding="utf-8") as f:
                        output_file.write(f.read())
                    self._increment_stat("processed")
                    self._add_file("text", relative_path)
                except (UnicodeDecodeError, IOError) as e:
                    self.logger.warning("Error reading file %s: %s", relative_path, e)
                    output_file.write(f"Error reading file: {e}\n")
                    self._increment_stat("skipped")
                output_file.write(f"\n{separator} END OF FILE {separator}\n")

        except IOError as e:
            self.logger.error("Error processing %s: %s", file_path, e)
            self._increment_stat("skipped")
            raise FileCombinatorError(f"Failed to process file: {e}") from e

    def generate_tree(self, start_path: str | Path, output_file: Any) -> None:
        """Generate a visual representation of the directory structure."""
        self.logger.info("Generating directory tree...")
        output_file.write("================== DIRECTORY STRUCTURE ==================\n")

        def write_tree(path: str | Path, prefix: str = "") -> None:
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
        self.logger.info("Directory tree generation completed")

    def process_directory(self, directory: str | Path, output_path: str) -> None:
        """Process a directory and combine its contents."""
        self.start_time = time.time()
        self.logger.info("Starting directory processing: %s", directory)

        temp_name = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", delete=False
            ) as temp_file:
                temp_name = temp_file.name
                self.logger.debug("Created temporary file: %s", temp_name)

                self.generate_tree(directory, temp_file)

                # Process all files
                for root, dirs, files in os.walk(directory):
                    dirs[:] = [
                        d
                        for d in dirs
                        if not self.is_excluded(Path(os.path.join(root, d)))
                    ]

                    for file in sorted(files):
                        file_path = os.path.join(root, file)
                        if not self.is_excluded(Path(file_path)):
                            self.process_file(file_path, temp_file)

            # Move temporary file to final location
            shutil.move(temp_name, output_path)

            # Print processing summary
            duration = time.time() - self.start_time
            self.logger.info("Processing completed in %.2f seconds", duration)
            self._log_statistics(output_path)

            # Show excluded files
            self._print_excluded_files()

        except OSError as e:
            self.logger.error("Fatal error during processing: %s", e)
            if temp_name and os.path.exists(temp_name):
                os.unlink(temp_name)
            raise FileCombinatorError(f"Failed to process directory: {e}") from e

    def _log_statistics(self, output_path: str) -> None:
        """Log processing statistics."""
        self.logger.info("Text files processed: %d", self.processed_files)
        self.logger.info("Binary files detected: %d", self.binary_files)
        self.logger.info("Image files detected: %d", self.image_files)
        self.logger.info("Files skipped due to errors: %d", self.skipped_files)
        self.logger.info("Output written to: %s", output_path)

    def _print_excluded_files(self) -> None:
        """Print information about excluded files."""
        for file_type, files in [
            ("Binary", self.binary_file_names),
            ("Image", self.image_file_names),
        ]:
            if files:
                print(f"\n{file_type} files detected and excluded:")
                for file_name in files:
                    print(f"  {file_name}")

    def _increment_stat(self, stat_name: str) -> None:
        """Increment a statistics counter."""
        setattr(self._stats, stat_name, getattr(self._stats, stat_name) + 1)

    def _add_file(self, file_type: str, filename: str) -> None:
        """Add a file to the appropriate tracking list."""
        getattr(self._files, file_type).append(filename)


def main() -> None:
    """Execute the FileCombinator CLI tool.

    This function parses command line arguments and runs the file combination process
    according to the specified options. It handles setup, validation, and execution
    of the file processing pipeline.
    """
    parser = argparse.ArgumentParser(
        description="Combine multiple files while preserving directory structure.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                            # Process current directory
  %(prog)s -d /path/to/dir            # Process specific directory
  %(prog)s -e node_modules dist       # Add custom exclusions
  %(prog)s -o combined_output.txt     # Specify output file
  %(prog)s -v                         # Enable verbose output
  %(prog)s --log-file logs/file.log   # Specify log file
        """,
    )

    parser.add_argument(
        "-d",
        "--directory",
        default=".",
        help="Directory to process (default: current directory)",
    )

    parser.add_argument(
        "-o",
        "--output",
        help="Output file name (default: <directory_name>_file_combinator_output.txt)",
    )

    parser.add_argument(
        "-e", "--exclude", nargs="+", help="Additional patterns to exclude"
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--log-file",
        default="logs/file_combinator.log",
        help="Log file path (default: logs/file_combinator.log)",
    )

    args = parser.parse_args()

    # Setup logging
    logger = FileCombinator.setup_logging(args.log_file, args.verbose)
    logger.info("File Combinator starting up...")
    logger.debug("Arguments: %s", vars(args))

    directory = os.path.abspath(args.directory)
    logger.debug("Processing directory: %s", directory)

    if args.output:
        output_file = args.output
    else:
        dir_name = os.path.basename(directory)
        output_file = f"{dir_name}_file_combinator_output.txt"

    logger.debug("Output file: %s", output_file)

    if os.path.exists(output_file):
        response = input(
            f"Output file '{output_file}' already exists. Overwrite? (y/n): "
        )
        if response.lower() != "y":
            logger.info("Operation cancelled by user")
            sys.exit(0)
        logger.debug("User confirmed file overwrite")

    try:
        # Create FileCombinator instance
        combinator = FileCombinator(
            additional_excludes=set(args.exclude) if args.exclude else None,
            verbose=args.verbose,
            output_file=output_file,
        )

        # Display banner
        combinator.display_banner()

        # Process the directory
        combinator.process_directory(directory, output_file)

    except (FileCombinatorError, IOError) as e:
        logger.error("Error during processing: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
