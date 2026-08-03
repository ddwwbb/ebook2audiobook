"""Tests for TXT chapter parser."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from e2a.parser import parse_txt_chapters


def test_parse_txt_with_chapters():
    content = """第一章 初遇

李明推开了门，屋里一片漆黑。

"你怎么还没睡？"他问。

第二章 真相

小雨转过身，目光复杂。

"我在等你。"她轻声说。

第三章 结局

天亮了。"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(content)
        path = f.name

    try:
        chapters = parse_txt_chapters(path)
        assert len(chapters) == 3
        assert "初遇" in chapters[0]["title"]
        assert "真相" in chapters[1]["title"]
        assert "结局" in chapters[2]["title"]
        assert "李明" in chapters[0]["text"]
        assert "小雨" in chapters[1]["text"]
    finally:
        Path(path).unlink()


def test_parse_txt_no_chapters():
    """No chapter headings → single chapter."""
    content = "这是一段没有章节标题的文本。"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(content)
        path = f.name

    try:
        chapters = parse_txt_chapters(path)
        assert len(chapters) == 1
        assert chapters[0]["index"] == 0
    finally:
        Path(path).unlink()


def test_parse_txt_numeric_chapters():
    content = """第1章 开始

内容一。

第2章 发展

内容二。"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(content)
        path = f.name

    try:
        chapters = parse_txt_chapters(path)
        assert len(chapters) == 2
    finally:
        Path(path).unlink()
