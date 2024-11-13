# filecombinator/processors/content.py
"""File content processing for FileCombinator."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, TextIO

from ..core.exceptions import FileProcessingError
from ..core.file_utils import FileTypeDetector, SafeOpen
from ..core.models import FileLists, FileStats

logger = logging.getLogger(__name__)


class ContentProcessor:
    """Handles file content processing and metadata collection."""

    def __init__(self) -> None:
        """Initialize ContentProcessor with file type detector."""
        self.file_type_detector = FileTypeDetector()
        self._stats = FileStats()
        self._files = FileLists()

    def get_file_info(self, file_path: str | Path) -> Dict[str, str]:
        """Get file information including size, modification time, and type.

        Args:
            file_path: Path to file to get info for

        Returns:
            Dict containing file metadata

        Raises:
            FileProcessingError: If there's an error getting file info
        """
        try:
            stat = os.stat(file_path)
            file_type = "Text"
            if self.file_type_detector.is_binary_file(file_path):
                file_type = "Binary"
            elif self.file_type_detector.is_image_file(file_path):
                file_type = "Image"

            return {
                "size": str(stat.st_size),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "type": file_type,
            }
        except (OSError, FileProcessingError) as e:
            logger.error("Error getting file info for %s: %s", file_path, e)
            raise FileProcessingError(f"Failed to get file info: {e}") from e

    def process_file(self, file_path: str | Path, output_file: TextIO) -> None:
        """Process a single file and write its content to output.

        Args:
            file_path: Path to file to process
            output_file: File object to write to

        Raises:
            FileProcessingError: If file can't be processed
        """
        try:
            relative_path = os.path.relpath(file_path)
            logger.debug("Processing file: %s", relative_path)

            try:
                file_info = self.get_file_info(file_path)
            except FileProcessingError:
                self._increment_stat("skipped")
                raise

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
                logger.info("Skipping content of image file: %s", relative_path)
            elif file_info["type"] == "Binary":
                output_file.write(
                    f"{separator} BINARY FILE (CONTENT EXCLUDED) {separator}\n"
                )
                self._increment_stat("binary")
                self._add_file("binary", relative_path)
                logger.info("Skipping content of binary file: %s", relative_path)
            else:
                output_file.write(f"{separator} START OF FILE {separator}\n")
                try:
                    with SafeOpen(file_path, "r", encoding="utf-8") as f:
                        output_file.write(f.read())
                    self._increment_stat("processed")
                    self._add_file("text", relative_path)
                except (UnicodeDecodeError, IOError, OSError) as e:
                    logger.warning("Error reading file %s: %s", relative_path, e)
                    output_file.write(f"Error reading file: {e}\n")
                    self._increment_stat("skipped")
                    raise FileProcessingError(f"Failed to read file: {e}") from e
                output_file.write(f"\n{separator} END OF FILE {separator}\n")
        except FileProcessingError:
            raise
        except Exception as e:
            logger.error("Error processing %s: %s", file_path, e)
            self._increment_stat("skipped")
            raise FileProcessingError(f"Failed to process file: {e}") from e

    def track_file(self, file_path: str | Path) -> None:
        """Track a file for statistics without processing its content.

        Args:
            file_path: Path to the file to track
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error("File does not exist: %s", file_path)
                self._increment_stat("skipped")
                return

            # Detect file type and track accordingly
            if self.file_type_detector.is_binary_file(file_path):
                self._increment_stat("binary")
                self._add_file("binary", str(file_path))
            elif self.file_type_detector.is_image_file(file_path):
                self._increment_stat("image")
                self._add_file("image", str(file_path))
            else:
                self._increment_stat("processed")
                self._add_file("text", str(file_path))
        except Exception as e:
            logger.error("Error tracking file %s: %s", file_path, e)
            self._increment_stat("skipped")

    def _increment_stat(self, stat_name: str) -> None:
        """Increment a statistics counter.

        Args:
            stat_name: Name of the stat to increment
        """
        setattr(self._stats, stat_name, getattr(self._stats, stat_name) + 1)

    def _add_file(self, file_type: str, filename: str) -> None:
        """Add a file to the appropriate tracking list.

        Args:
            file_type: Type of file (text, binary, image)
            filename: Name of the file
        """
        getattr(self._files, file_type).append(filename)

    @property
    def stats(self) -> FileStats:
        """Get current file processing statistics."""
        return self._stats

    @property
    def file_lists(self) -> FileLists:
        """Get current file lists."""
        return self._files
