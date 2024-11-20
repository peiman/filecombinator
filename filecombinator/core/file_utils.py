# filecombinator/core/file_utils.py
"""File utility functions and classes for FileCombinator."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from types import TracebackType
from typing import Any, Optional, Set, Type

from .exceptions import FileProcessingError

logger = logging.getLogger(__name__)

# Try to import magic, but don't fail if it's not available
try:
    import magic

    MAGIC_AVAILABLE = True
except ImportError:  # pragma: no cover
    MAGIC_AVAILABLE = False
    logger.debug(
        "python-magic library not available, falling back to basic type detection"
    )


class SafeOpen:
    """Context manager for safely opening files with proper resource management."""

    def __init__(
        self,
        file_path: str | Path,
        mode: str = "r",
        encoding: str = "utf-8",
        **kwargs: Any,
    ) -> None:
        """Initialize the context manager with proper encoding by default.

        Args:
            file_path: Path to the file to open
            mode: File mode (e.g., 'r', 'w', 'rb')
            encoding: Character encoding for text files
            **kwargs: Additional arguments to pass to open()
        """
        self.file_path = file_path
        self.mode = mode
        self.kwargs = kwargs
        if "b" not in mode:
            self.kwargs["encoding"] = encoding
        self.file_obj: Any = None

    def __enter__(self) -> Any:
        """Open and return the file object with proper encoding.

        Returns:
            File object

        Raises:
            IOError: If file cannot be opened
        """
        try:
            self.file_obj = open(self.file_path, self.mode, **self.kwargs)
            return self.file_obj
        except IOError as e:
            logger.error("Failed to open file %s: %s", self.file_path, e)
            raise

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Close the file object even if an exception occurred.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        if self.file_obj is not None:
            try:
                self.file_obj.close()
            except Exception as e:  # pragma: no cover
                logger.warning("Error closing file %s: %s", self.file_path, e)


class FileTypeDetector:
    """Handles file type detection and categorization."""

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

    # Known text file extensions
    TEXT_EXTENSIONS: Set[str] = {
        ".txt",
        ".json",
        ".xml",
        ".yaml",
        ".yml",
        ".md",
        ".py",
        ".js",
        ".html",
        ".css",
        ".csv",
        ".log",
        ".ini",
        ".conf",
        ".toml",
    }

    # Known text MIME types
    TEXT_MIME_TYPES: Set[str] = {
        "text/",
        "application/json",
        "application/x-ndjson",  # Added for newline-delimited JSON
        "application/xml",
        "application/x-empty",
        "application/x-yaml",
        "application/x-javascript",
        "application/javascript",
        "inode/x-empty",
    }

    def __init__(self) -> None:
        """Initialize the FileTypeDetector."""
        self.mime: Optional[Any] = None
        if MAGIC_AVAILABLE:
            try:
                self.mime = magic.Magic(mime=True)
                logger.debug("Magic library initialized successfully")
            except Exception as e:  # pragma: no cover
                logger.debug("Could not initialize magic library: %s", e)
                self.mime = None

    def _check_for_binary_content(self, chunk: bytes) -> bool:
        """Check if content chunk appears to be binary.

        Args:
            chunk: Bytes to check

        Returns:
            bool: True if content appears binary, False otherwise
        """
        # Empty content is considered text
        if not chunk:
            return False

        # Check for null bytes
        if b"\x00" in chunk:
            logger.debug("Found null bytes in content")
            return True

        # Try to decode as text
        try:
            chunk.decode("utf-8", errors="strict")
            return False
        except UnicodeDecodeError:
            logger.debug("Content failed UTF-8 decoding")
            return True

    def _read_file_chunk(self, file_path: str) -> bytes:
        """Read a chunk of file content safely.

        Args:
            file_path: Path to the file to read

        Returns:
            bytes: The read chunk of data

        Raises:
            FileProcessingError: If there's an error reading the file
        """
        try:
            with open(file_path, "rb") as f:
                return f.read(8192)
        except IOError as e:
            logger.error("Error reading file %s: %s", file_path, e)
            raise FileProcessingError(f"Error reading file {file_path}: {e}")

    def is_image_file(self, file_path: str | Path) -> bool:
        """Check if a file is an image.

        Args:
            file_path: Path to the file to check

        Returns:
            bool: True if the file is an image, False otherwise
        """
        file_path_str = str(file_path)
        if not os.path.exists(file_path_str):
            logger.debug("File %s does not exist", file_path_str)
            return False

        # Check extension first
        extension = Path(file_path_str).suffix.lower()
        if extension in self.IMAGE_EXTENSIONS:
            logger.debug("File %s identified as image by extension", file_path_str)
            return True

        # Try MIME type detection
        if self.mime:
            try:
                mime_type = self.mime.from_file(file_path_str)
                if mime_type.startswith("image/"):
                    logger.debug(
                        "File %s identified as image by MIME type", file_path_str
                    )
                    return True
            except Exception as e:
                logger.warning("Error checking MIME type for %s: %s", file_path_str, e)

        return False

    def is_binary_file(self, file_path: str | Path) -> bool:
        """Detect if a file is binary.

        Args:
            file_path: Path to the file to check

        Returns:
            bool: True if the file is binary, False otherwise

        Raises:
            FileProcessingError: If there's an error reading the file
        """
        file_path_str = str(file_path)
        logger.debug("Checking if file is binary: %s", file_path_str)

        if not os.path.exists(file_path_str):
            logger.error("File does not exist: %s", file_path_str)
            raise FileProcessingError(f"File does not exist: {file_path_str}")

        # Empty files are treated as text files
        size = os.path.getsize(file_path_str)
        logger.debug("File size: %d bytes", size)
        if size == 0:
            logger.debug("Empty file %s treated as text", file_path_str)
            return False

        # For .txt files, always check content regardless of MIME type
        extension = Path(file_path_str).suffix.lower()
        logger.debug("File extension: %s", extension)
        if extension == ".txt":
            logger.debug("Text file found, will check content regardless of MIME type")
        else:
            # For non-txt files, check known extensions first
            if extension in self.TEXT_EXTENSIONS:
                logger.debug("File %s identified as text by extension", file_path_str)
                return False
            if extension in self.BINARY_EXTENSIONS:
                logger.debug("File %s identified as binary by extension", file_path_str)
                return True

            # Then try MIME type detection
            if self.mime:
                try:
                    mime_type = self.mime.from_file(file_path_str)
                    logger.debug("MIME type for %s: %s", file_path_str, mime_type)

                    # Check for text MIME types
                    for text_mime in self.TEXT_MIME_TYPES:
                        if mime_type.startswith(text_mime):
                            logger.debug(
                                "File %s identified as text by MIME type %s",
                                file_path_str,
                                mime_type,
                            )
                            return False
                    logger.debug("No matching text MIME type found")
                except Exception as e:
                    logger.warning(
                        "Error checking mime type for %s: %s", file_path_str, e
                    )

        # For .txt files and files not identified by extension or MIME type,
        # check content
        logger.debug("Performing content analysis")
        try:
            chunk = self._read_file_chunk(file_path_str)
            is_binary = self._check_for_binary_content(chunk)
            logger.debug(
                "Content analysis result for %s: %s",
                file_path_str,
                "binary" if is_binary else "text",
            )
            return is_binary
        except Exception as e:
            logger.error("Error during binary detection: %s", e, exc_info=True)
            raise FileProcessingError(f"Error reading file {file_path_str}: {e}")
