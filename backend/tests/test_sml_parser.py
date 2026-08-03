"""Tests for SML parser."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from audio.sml_parser import parse_sml


def test_voice_tag():
    sml = "[voice:李明]你怎么还没睡？[/voice]"
    segs = parse_sml(sml)
    assert len(segs) == 1
    assert segs[0].kind == "text"
    assert segs[0].text == "你怎么还没睡？"
    assert segs[0].voice == "李明"


def test_pause_tags():
    sml = "你好[pause:0.5]世界[break]"
    segs = parse_sml(sml)
    assert len(segs) == 4
    assert segs[0].text == "你好"
    assert segs[1].kind == "pause"
    assert segs[1].pause_seconds == 0.5
    assert segs[2].text == "世界"
    assert segs[3].kind == "pause"
    assert segs[3].pause_seconds == 0.4


def test_default_voice():
    sml = "旁白文本"
    segs = parse_sml(sml, default_voice="旁白")
    assert len(segs) == 1
    assert segs[0].voice == "旁白"


def test_voice_switch():
    sml = (
        "[voice:旁白]李明推开门。[/voice]\n"
        "[voice:李明]谁？[/voice]"
    )
    segs = parse_sml(sml)
    texts = [(s.voice, s.text) for s in segs if s.kind == "text"]
    assert texts == [("旁白", "李明推开门。"), ("李明", "谁？")]
