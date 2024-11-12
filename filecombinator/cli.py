# filecombinator/cli.py
"""Command line interface for FileCombinator."""

import argparse
import logging
import os
import sys
from typing import Optional, Sequence

from .core.combinator import FileCombinator
from .core.exceptions import FileCombinatorError

logger = logging.getLogger(__name__)


def parse_args(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        args: Command line arguments

    Returns:
        Parsed arguments namespace
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

    return parser.parse_args(args)


def main(args: Optional[Sequence[str]] = None) -> int:
    """Execute the FileCombinator CLI tool.

    Args:
        args: Command line arguments

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    parsed_args = parse_args(args)

    # Setup logging
    logger = FileCombinator.setup_logging(parsed_args.log_file, parsed_args.verbose)
    logger.info("File Combinator starting up...")
    logger.debug("Arguments: %s", vars(parsed_args))

    directory = os.path.abspath(parsed_args.directory)
    logger.debug("Processing directory: %s", directory)

    if parsed_args.output:
        output_file = parsed_args.output
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
            return 0
        logger.debug("User confirmed file overwrite")

    try:
        # Create FileCombinator instance
        combinator = FileCombinator(
            additional_excludes=(
                set(parsed_args.exclude) if parsed_args.exclude else None
            ),
            verbose=parsed_args.verbose,
            output_file=output_file,
        )

        # Display banner
        combinator.display_banner()

        # Process the directory
        combinator.process_directory(directory, output_file)
        return 0

    except FileCombinatorError as e:
        logger.error("Error during processing: %s", e)
        return 1
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
