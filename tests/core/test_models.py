# tests/core/test_models.py
"""Test suite for FileCombinator data models."""

from filecombinator.core.models import FileLists, FileStats


def test_file_stats_initialization() -> None:
    """Test FileStats initialization with default values."""
    stats = FileStats()
    assert stats.processed == 0
    assert stats.skipped == 0
    assert stats.binary == 0
    assert stats.image == 0


def test_file_stats_increment() -> None:
    """Test FileStats counter increments."""
    stats = FileStats(processed=1, skipped=2, binary=3, image=4)
    assert stats.processed == 1
    assert stats.skipped == 2
    assert stats.binary == 3
    assert stats.image == 4


def test_file_lists_initialization() -> None:
    """Test FileLists initialization with empty lists."""
    lists = FileLists()
    assert lists.text == []
    assert lists.binary == []
    assert lists.image == []


def test_file_lists_append() -> None:
    """Test FileLists appending functionality."""
    lists = FileLists()
    lists.text.append("test.txt")
    lists.binary.append("test.bin")
    lists.image.append("test.jpg")

    assert "test.txt" in lists.text
    assert "test.bin" in lists.binary
    assert "test.jpg" in lists.image
