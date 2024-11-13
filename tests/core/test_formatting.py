# tests/core/test_formatting.py
"""Test suite for FileCombinator output formatting functionality."""

import os
from io import StringIO

from filecombinator.core.formatting import FormatProcessor


def test_ai_instructions_header_content() -> None:
    """Test that AI instructions match the template file."""
    processor = FormatProcessor()
    output = StringIO()

    # Get the template content directly from the file
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "filecombinator",
        "core",
        "templates",
        "ai_instructions.md",
    )

    with open(template_path, "r", encoding="utf-8") as f:
        expected_content = f.read()

    processor.write_header(output)
    actual_content = output.getvalue()

    assert actual_content.strip() == expected_content.strip()
