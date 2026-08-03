"""Tests for two-pass pipeline."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.two_pass import _select_sample_chapters
from pipeline.types import Chapter


def test_select_sample_small():
    """Fewer chapters than sample_count → return all."""
    chapters = [Chapter(index=i, title=f"Ch{i}", text="x") for i in range(3)]
    result = _select_sample_chapters(chapters, sample_count=5)
    assert len(result) == 3


def test_select_sample_large():
    """More chapters than sample_count → return sample_count."""
    chapters = [Chapter(index=i, title=f"Ch{i}", text="x") for i in range(20)]
    result = _select_sample_chapters(chapters, sample_count=5)
    assert len(result) == 5
    # First and last should always be included
    assert result[0].index == 0
    assert result[1].index == 19


def test_select_sample_exact():
    """Exactly sample_count chapters → return all."""
    chapters = [Chapter(index=i, title=f"Ch{i}", text="x") for i in range(5)]
    result = _select_sample_chapters(chapters, sample_count=5)
    assert len(result) == 5


def test_select_sample_two():
    """Two chapters → both returned."""
    chapters = [Chapter(index=0, title="A", text="x"), Chapter(index=1, title="B", text="y")]
    result = _select_sample_chapters(chapters, sample_count=5)
    assert len(result) == 2
