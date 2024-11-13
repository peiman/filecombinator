# tests/core/test_console.py
"""Test suite for FileCombinator rich console output."""

import io
from typing import Tuple
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from filecombinator.core.console import (
    create_file_table,
    create_stats_panel,
    print_banner,
    print_error,
    print_success,
    print_warning,
)


@pytest.fixture
def mock_console() -> Tuple[Console, io.StringIO]:
    """Create a mock console with StringIO for testing output.

    Returns:
        Tuple containing Console and StringIO objects
    """
    string_io = io.StringIO()
    console = Console(file=string_io, force_terminal=True, color_system=None)
    return console, string_io


def test_print_banner(mock_console: Tuple[Console, io.StringIO]) -> None:
    """Test banner printing with Rich styling."""
    console, string_io = mock_console
    banner_text = "Test Banner"

    with patch("filecombinator.core.console.console", console):
        print_banner(banner_text)

    output = string_io.getvalue()
    assert "Test Banner" in output
    assert "─" in output  # Panel border


def test_print_success(mock_console: Tuple[Console, io.StringIO]) -> None:
    """Test success message printing."""
    console, string_io = mock_console
    message = "Operation successful"

    with patch("filecombinator.core.console.console", console):
        print_success(message)

    output = string_io.getvalue()
    assert "Operation successful" in output
    assert "✓" in output


def test_print_error(mock_console: Tuple[Console, io.StringIO]) -> None:
    """Test error message printing."""
    console, string_io = mock_console
    message = "Error occurred"

    with patch("filecombinator.core.console.error_console", console):
        print_error(message)

    output = string_io.getvalue()
    assert "Error occurred" in output
    assert "✗" in output


def test_print_warning(mock_console: Tuple[Console, io.StringIO]) -> None:
    """Test warning message printing."""
    console, string_io = mock_console
    message = "Warning message"

    with patch("filecombinator.core.console.console", console):
        print_warning(message)

    output = string_io.getvalue()
    assert "Warning message" in output
    assert "⚠" in output


def test_create_stats_panel() -> None:
    """Test statistics panel creation."""
    stats = MagicMock(
        processed=10,
        binary=2,
        image=3,
        skipped=1,
    )
    output_file = "test_output.txt"

    panel = create_stats_panel(stats, output_file)

    assert isinstance(panel, Panel)
    # Create a console to test the content
    test_console = Console(color_system=None)
    with test_console.capture() as capture:
        test_console.print(panel)
    output = capture.get()

    assert "10" in output  # Processed files count
    assert "2" in output  # Binary files count
    assert "3" in output  # Image files count
    assert "1" in output  # Skipped files count
    assert "test_output.txt" in output


def test_create_file_table() -> None:
    """Test file table creation."""
    files = ["file1.txt", "file2.py", "file3.jpg"]
    file_type = "Text Files"

    table = create_file_table(files, file_type)

    assert isinstance(table, Table)
    # Create a console to test the content
    test_console = Console(color_system=None)
    with test_console.capture() as capture:
        test_console.print(table)
    output = capture.get()

    assert "file1.txt" in output
    assert "file2.py" in output
    assert "file3.jpg" in output
    assert file_type in output


def test_create_file_table_with_max_files() -> None:
    """Test file table creation with maximum files limit."""
    files = ["file1.txt", "file2.py", "file3.jpg", "file4.png"]
    file_type = "Text Files"
    max_files = 2

    table = create_file_table(files, file_type, max_files)
    test_console = Console(color_system=None)
    with test_console.capture() as capture:
        test_console.print(table)
    output = capture.get()

    assert "file1.txt" in output
    assert "file2.py" in output
    assert "2 more files" in output
    assert "file4.png" not in output
