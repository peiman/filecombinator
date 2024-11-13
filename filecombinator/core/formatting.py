# filecombinator/core/formatting.py
"""Formatting processor for FileCombinator output."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, TextIO

from ..core.exceptions import FileProcessingError
from ..core.file_utils import FileTypeDetector, SafeOpen

logger = logging.getLogger(__name__)


class FormatProcessor:
    """Handles formatting of FileCombinator output."""

    def __init__(self) -> None:
        """Initialize the format processor."""
        self.extension_to_language: Dict[str, str] = {
            ".py": "python",
            ".js": "javascript",
            ".java": "java",
            ".html": "html",
            ".css": "css",
            ".md": "markdown",
            ".txt": "text",
            ".sh": "bash",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".xml": "xml",
            ".sql": "sql",
            ".rs": "rust",
            ".go": "go",
            ".rb": "ruby",
            ".php": "php",
            ".ts": "typescript",
            ".jsx": "jsx",
            ".tsx": "tsx",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".ini": "ini",
            ".toml": "toml",
            ".cfg": "ini",
        }
        self.file_type_detector = FileTypeDetector()

    def detect_language(self, file_path: str | Path) -> str:
        """Detect programming language based on file extension.

        Args:
            file_path: Path to the file

        Returns:
            str: Language identifier for syntax highlighting
        """
        ext = os.path.splitext(str(file_path))[1].lower()
        return self.extension_to_language.get(ext, "text")

    def write_header(self, output: TextIO) -> None:
        """Write AI instructions header to output.

        Args:
            output: Output file to write to

        Raises:
            FileProcessingError: If instructions template cannot be read
        """
        try:
            template_path = os.path.join(
                os.path.dirname(__file__), "templates", "ai_instructions.md"
            )
            with SafeOpen(template_path, "r") as f:
                output.write(f.read())
        except (IOError, OSError) as e:
            logger.error("Failed to read AI instructions template: %s", e)
            raise FileProcessingError(f"Failed to read AI instructions: {e}") from e

    def format_file_section(self, file_path: str | Path, output: TextIO) -> None:
        """Format a file section including metadata and content.

        Args:
            file_path: Path to the file to process
            output: Output file to write to

        Raises:
            FileProcessingError: If file cannot be processed
        """
        if not os.path.exists(file_path):
            logger.error("File does not exist: %s", file_path)
            raise FileProcessingError(f"File does not exist: {file_path}")

        try:
            # Get file info
            stat = os.stat(file_path)
            modified = datetime.fromtimestamp(stat.st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            file_type = "Text"

            if self.file_type_detector.is_binary_file(file_path):
                file_type = "Binary"
            elif self.file_type_detector.is_image_file(file_path):
                file_type = "Image"

            # Write header with relative path
            rel_path = os.path.relpath(file_path)
            output.write(f"\n## File: `{rel_path}`\n\n")

            # Write metadata
            output.write("**Metadata**:\n\n")
            output.write(f"- **Type**: {file_type}\n")
            output.write(f"- **Size**: {stat.st_size} bytes\n")
            output.write(f"- **Last Modified**: {modified}\n\n")

            # Write content or placeholder
            if file_type == "Binary":
                output.write("*Content excluded: Binary file*\n")
            elif file_type == "Image":
                output.write("*Content excluded: Image file*\n")
            else:
                language = self.detect_language(file_path)
                output.write(f"`````{language}\n")
                try:
                    with SafeOpen(file_path, "r", encoding="utf-8") as f:
                        output.write(f.read())
                except UnicodeDecodeError as e:
                    logger.error("Failed to decode file %s: %s", file_path, e)
                    raise FileProcessingError(f"Failed to decode file: {e}") from e
                output.write("\n`````")

            # Add section separator
            output.write("\n\n---\n")

        except (OSError, IOError) as e:
            logger.error("Error processing file %s: %s", file_path, e)
            raise FileProcessingError(f"Failed to process file: {e}") from e

    def format_directory_tree(self, tree_content: str, output: TextIO) -> None:
        """Format the directory tree section.

        Args:
            tree_content: Directory tree content to format
            output: Output file to write to
        """
        output.write("## Directory Structure\n\n")
        if tree_content:
            output.write("`````plaintext\n")
            output.write(tree_content.strip())
            output.write("\n`````")
        output.write("\n\n---\n")
