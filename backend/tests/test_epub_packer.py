"""Tests for EPUB packer."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packer.epub_packer import pack_epub


def test_pack_epub_basic():
    """Pack a minimal EPUB and verify it's a valid zip."""
    import zipfile

    chapters = [
        ("第一章", "[voice:旁白]这是旁白。[/voice]\n[voice:李明]你好。[/voice]"),
        ("第二章", "[voice:旁白]第二章内容。[/voice]"),
    ]
    voices_map = {
        "旁白": {"engine": "edge", "voice_id": "zh-CN-XiaoyiNeural"},
        "李明": {"engine": "edge", "voice_id": "zh-CN-YunxiNeural"},
    }

    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "test.epub"
        result = pack_epub(
            title="测试书",
            author="测试作者",
            chapters=chapters,
            voices_map=voices_map,
            output_path=str(output),
        )
        assert Path(result).exists()
        assert Path(result).stat().st_size > 0

        # Verify it's a valid zip/epub
        with zipfile.ZipFile(result, "r") as zf:
            names = zf.namelist()
            assert "META-INF/container.xml" in names
            assert any("chap_000" in n for n in names)
            assert any("chap_001" in n for n in names)
            assert any(n.endswith("voices.json") for n in names)

            # Check voices.json content
            vj_name = next(n for n in names if n.endswith("voices.json"))
            vj = json.loads(zf.read(vj_name))
            assert "旁白" in vj
            assert "李明" in vj


def test_pack_epub_no_voices():
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "no_voices.epub"
        result = pack_epub(
            title="简单书",
            chapters=[("唯一章节", "内容")],
            output_path=str(output),
        )
        assert Path(result).exists()
