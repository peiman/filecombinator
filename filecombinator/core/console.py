# filecombinator/core/console.py
"""Rich console output functionality for FileCombinator."""

from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text

from ..core.models import FileStats

# Create console with support for both terminal and non-terminal environments
console = Console()
error_console = Console(stderr=True)


def print_banner(text: str) -> None:
    """Print a styled banner using Rich.

    Args:
        text: Text to display in banner
    """
    if not console.is_terminal:
        console.print(text)
        return

    styled_text = Text(text)
    styled_text.stylize(Style(color="blue", bold=True))
    console.print(Panel(styled_text, border_style="blue"))


def print_success(message: str) -> None:
    """Print a success message using Rich.

    Args:
        message: Success message to display
    """
    console.print("[green]✓ " + message + "[/green]")


def print_error(message: str) -> None:
    """Print an error message using Rich.

    Args:
        message: Error message to display
    """
    error_console.print("[red]✗ " + message + "[/red]")


def print_warning(message: str) -> None:
    """Print a warning message using Rich.

    Args:
        message: Warning message to display
    """
    console.print("[yellow]⚠ " + message + "[/yellow]")


def create_stats_panel(stats: FileStats, output_file: str) -> Panel:
    """Create a Rich panel displaying processing statistics.

    Args:
        stats: Processing statistics
        output_file: Path to output file

    Returns:
        Rich Panel containing formatted statistics
    """
    # Create the content for the panel
    content = [
        Text("Processing Statistics\n\n", style="bold"),
        Text("Text files processed: ", style="bold"),
        Text(str(stats.processed) + "\n", style="green"),
        Text("Binary files detected: ", style="bold"),
        Text(str(stats.binary) + "\n", style="blue"),
        Text("Image files detected: ", style="bold"),
        Text(str(stats.image) + "\n", style="magenta"),
        Text("Files skipped: ", style="bold"),
        Text(str(stats.skipped) + "\n", style="yellow"),
        Text("\nOutput written to: ", style="bold"),
        Text(output_file, style="blue underline"),
    ]

    # Combine all text elements
    stats_text = Text().join(content)

    return Panel(
        stats_text,
        title="Results",
        border_style="blue",
        padding=(1, 2),
    )


def create_file_table(
    files: List[str], file_type: str, max_files: Optional[int] = None
) -> Table:
    """Create a Rich table displaying processed files.

    Args:
        files: List of file paths
        file_type: Type of files being displayed
        max_files: Optional maximum number of files to display

    Returns:
        Rich Table containing file information
    """
    table = Table(
        title=file_type,
        show_header=True,
        header_style="bold blue",
        border_style="blue",
        title_justify="left",
    )

    table.add_column("File Path", style="dim", no_wrap=True)
    table.add_column("Status", justify="right", style="green")

    display_files = files[:max_files] if max_files else files
    for file_path in display_files:
        table.add_row(file_path, "✓ Processed")

    if max_files and len(files) > max_files:
        remaining = len(files) - max_files
        table.add_row("... and " + str(remaining) + " more files", style="dim italic")

    return table
