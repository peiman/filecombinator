"""Command line interface for FileCombinator."""

import logging
import os
import sys
from typing import Optional, TextIO

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from . import __version__
from .core.banner import get_banner
from .core.combinator import FileCombinator
from .core.config import get_config
from .core.console import (
    create_file_table,
    create_stats_panel,
    print_banner,
    print_error,
    print_success,
    print_warning,
)
from .core.exceptions import FileCombinatorError

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False, style: bool = True) -> None:
    """Set up logging with Rich formatting."""
    log_handler = (
        RichHandler(
            rich_tracebacks=True,
            markup=style,
            show_time=False,
            show_path=False,
        )
        if style
        else logging.StreamHandler(sys.stderr)
    )

    log_handler.setFormatter(logging.Formatter("%(message)s"))

    logger = logging.getLogger()
    logger.handlers = []  # Remove existing handlers
    logger.addHandler(log_handler)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)


def check_output_file(output_path: str, stdin: TextIO = sys.stdin) -> bool:
    """Check if output file exists and confirm overwrite."""
    if os.path.exists(output_path) and stdin.isatty():
        return bool(
            click.confirm(
                f"Output file '{output_path}' already exists. Overwrite?", default=True
            )
        )
    return True


def display_summary(
    combinator: FileCombinator, output_file: str, style: bool = True, max_files: int = 5
) -> None:
    """Display processing summary with Rich formatting."""
    stats = combinator.stats
    file_lists = combinator.file_lists

    print_success("\nProcessing completed!")

    if style:
        console = Console()
        console.print(create_stats_panel(stats, output_file))

        if stats.processed > 0:
            console.print(
                create_file_table(file_lists.text, "Text Files Processed", max_files)
            )
        if stats.binary > 0:
            console.print(
                create_file_table(file_lists.binary, "Binary Files Detected", max_files)
            )
        if stats.image > 0:
            console.print(
                create_file_table(file_lists.image, "Image Files Detected", max_files)
            )
    else:
        # Fallback for non-styled output
        print("\nStatistics:")
        print(f"Text files processed: {stats.processed}")
        print(f"Binary files detected: {stats.binary}")
        print(f"Image files detected: {stats.image}")
        print(f"Files skipped: {stats.skipped}")
        print(f"Output written to: {output_file}")

    if stats.skipped > 0:
        print_warning(f"Skipped {stats.skipped} files due to errors")


def process_directory(
    directory: str,
    output: str,
    exclude: tuple[str, ...],
    verbose: bool,
    style: bool = True,
) -> None:
    """Process directory and generate output."""
    combinator = FileCombinator(
        additional_excludes=set(exclude) if exclude else None,
        verbose=verbose,
        output_file=output,
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        disable=not style or not sys.stdout.isatty(),
    ) as progress:
        task = progress.add_task("Processing files...", total=None)
        combinator.process_directory(directory, output)
        progress.update(task, completed=True)

    display_summary(combinator, output, style)


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
    help="Output file path (default: <directory_name><configured_suffix>)",
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
    """Combine multiple files while preserving directory structure."""
    try:
        if not os.path.exists(directory):
            raise FileCombinatorError(f"Directory not found: {directory}")

        if style:
            print_banner(get_banner())

        setup_logging(verbose, style)

        config = get_config()
        suffix = config.output_suffix
        if not output:
            dir_name = os.path.basename(os.path.abspath(directory))
            output = f"{dir_name}{suffix}"
        elif not os.path.splitext(output)[1]:
            output = f"{output}{suffix}"

        if not check_output_file(output):
            print_warning("Operation cancelled by user")
            sys.exit(0)

        process_directory(directory, output, exclude, verbose, style)

    except FileCombinatorError as e:
        print_error(str(e))
        sys.exit(2)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        if verbose:
            logger.exception("Detailed error information:")
        sys.exit(2)


# For backward compatibility and entry point
cli = main

if __name__ == "__main__":  # pragma: no cover
    main()
