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

    def is_image_file(self, file_path: str | Path) -> bool:
        """Check if a file is an image.

        Args:
            file_path: Path to the file to check

        Returns:
            bool: True if the file is an image, False otherwise
        """
        if self.mime:
            try:
                mime_type = self.mime.from_file(str(file_path))
                if mime_type.startswith("image/"):
                    return True
            except Exception as e:
                logger.debug("Error checking mime type: %s", e)

        return Path(file_path).suffix.lower() in self.IMAGE_EXTENSIONS

    def is_binary_file(self, file_path: str | Path) -> bool:
        """Detect if a file is binary.

        Args:
            file_path: Path to the file to check

        Returns:
            bool: True if the file is binary, False otherwise

        Raises:
            FileProcessingError: If there's an error reading the file
        """
        if not os.path.exists(file_path):
            raise FileProcessingError(f"File does not exist: {file_path}")

        # Empty files are treated as text files
        if os.path.getsize(file_path) == 0:
            return False

        if Path(file_path).suffix.lower() in self.BINARY_EXTENSIONS:
            return True

        if self.mime:
            try:
                mime_type = self.mime.from_file(str(file_path))
                # Treat standard text formats as non-binary
                return not any(
                    mime_type.startswith(prefix)
                    for prefix in [
                        "text/",
                        "application/json",
                        "application/xml",
                        "application/x-empty",
                    ]
                )
            except Exception as e:  # pragma: no cover
                logger.debug("Error checking mime type: %s", e)
                # Fall back to alternative detection method

        # Fallback binary detection
        try:
            chunk_size = 8192  # Increased for better detection
            with SafeOpen(file_path, "rb") as f:
                chunk = f.read(chunk_size)
                # Consider files with null bytes as binary
                if b"\x00" in chunk:
                    return True
                # Try to decode as text
                try:
                    chunk.decode("utf-8")
                    return False
                except UnicodeDecodeError:
                    return True
        except IOError as e:  # pragma: no cover
            logger.debug("Error reading file: %s", e)
            raise FileProcessingError(f"Error reading file {file_path}: {e}") from e
