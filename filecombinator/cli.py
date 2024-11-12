# filecombinator/cli.py
"""Command line interface for FileCombinator."""

import logging
import os
import sys
from typing import Optional

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.style import Style
from rich.text import Text

from . import __version__
from .core.banner import get_banner
from .core.combinator import FileCombinator
from .core.exceptions import FileCombinatorError

# Create console with color system that respects --style flag
console = Console(force_terminal=False)
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False, style: bool = True) -> None:
    """Set up logging with Rich formatting.

    Args:
        verbose: Whether to enable debug logging
        style: Whether to enable rich styling
    """
    log_handler = (
        RichHandler(
            console=console,
            rich_tracebacks=True,
            markup=style,
            show_time=False,
        )
        if style
        else logging.StreamHandler(sys.stderr)
    )

    log_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    logger = logging.getLogger()
    logger.handlers = []  # Remove existing handlers
    logger.addHandler(log_handler)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)


def display_banner(style: bool = True) -> None:
    """Display the application banner with optional styling.

    Args:
        style: Whether to apply Rich styling
    """
    banner = get_banner()
    if style and console.is_terminal:
        styled_banner = Text(banner)
        styled_banner.stylize(Style(color="blue", bold=True))
        console.print(Panel(styled_banner))
    else:
        click.echo(banner)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "-d",
    "--directory",
    default=".",
    help="Directory to process (default: current directory)",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
)
@click.option(
    "-o",
    "--output",
    help="Output file name (default: <directory_name>_file_combinator_output.txt)",
    type=click.Path(dir_okay=False),
)
@click.option(
    "-e",
    "--exclude",
    multiple=True,
    help="Additional patterns to exclude (can be used multiple times)",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.option("--style/--no-style", default=True, help="Enable/disable rich styling")
@click.version_option(version=__version__, prog_name="FileCombinator")
def main(
    directory: str,
    output: Optional[str],
    exclude: tuple[str, ...],
    verbose: bool,
    style: bool,
) -> None:
    """Combine multiple files while preserving directory structure.

    This tool processes files in the specified directory, combining them into a
    single output file while maintaining their original structure and metadata.
    """
    try:
        # Set up logging with Rich
        setup_logging(verbose, style)

        if not os.path.exists(directory):
            raise FileCombinatorError(f"Directory not found: {directory}")

        # Display banner
        display_banner(style)

        # Initialize FileCombinator
        combinator = FileCombinator(
            additional_excludes=set(exclude) if exclude else None,
            verbose=verbose,
            output_file=output,
        )

        # Determine output file name if not provided
        if not output:
            dir_name = os.path.basename(os.path.abspath(directory))
            output = f"{dir_name}_file_combinator_output.txt"

        # Confirm overwrite if file exists
        if os.path.exists(output) and sys.stdin.isatty():
            if not click.confirm(
                f"Output file '{output}' already exists. Overwrite?",
                default=True,
            ):
                click.echo("Operation cancelled by user")
                sys.exit(0)

        # Process directory with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console if style and console.is_terminal else None,
            disable=not style or not console.is_terminal,
        ) as progress:
            task = progress.add_task("Processing files...", total=None)
            # Process the directory
            combinator.process_directory(directory, output)
            progress.update(task, completed=True)

        # Display results
        stats = combinator.stats
        if style and console.is_terminal:
            click.echo()  # Add newline
            console.print("[bold green]Processing completed![/bold green]")
            console.print(
                Panel.fit(
                    f"""[bold]Statistics:[/bold]
• Text files processed: {stats.processed}
• Binary files detected: {stats.binary}
• Image files detected: {stats.image}
• Files skipped: {stats.skipped}
• Output written to: {output}""",
                    title="Results",
                    border_style="blue",
                )
            )
        else:
            click.echo("\nProcessing completed!")
            click.echo(f"\nText files processed: {stats.processed}")
            click.echo(f"Binary files detected: {stats.binary}")
            click.echo(f"Image files detected: {stats.image}")
            click.echo(f"Files skipped: {stats.skipped}")
            click.echo(f"Output written to: {output}")

    except FileCombinatorError as e:
        logger.error(str(e))
        sys.exit(2)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=verbose)
        sys.exit(2)


cli = main  # For backwards compatibility

if __name__ == "__main__":  # pragma: no cover
    main()
