"""Tests for pipeline prompt rendering and role merging."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from llm.prompts import load_prompt, render_prompt
from pipeline.single_pass import _format_known_roles, _merge_roles, _split_long_text
from pipeline.types import Role


def test_load_prompt():
    tpl = load_prompt("single_pass")
    assert "{{chapter_text}}" in tpl
    assert "{{known_roles}}" in tpl


def test_render_prompt():
    tpl = "Hello {{name}}, you are {{role}}"
    result = render_prompt(tpl, name="李明", role="主角")
    assert result == "Hello 李明, you are 主角"


def test_render_prompt_no_placeholders():
    tpl = "No placeholders here"
    result = render_prompt(tpl)
    assert result == tpl


def test_format_known_roles_empty():
    assert "暂无" in _format_known_roles([])


def test_format_known_roles():
    roles = [
        Role(name="李明", gender="male", age="adult", aliases=["小李"]),
        Role(name="小雨", gender="female", age="adult"),
    ]
    result = _format_known_roles(roles)
    assert "李明" in result
    assert "小雨" in result
    assert "小李" in result


def test_merge_roles_new():
    existing = [Role(name="李明", gender="male")]
    new = [{"name": "小雨", "gender": "female", "age": "adult"}]
    result = _merge_roles(existing, new)
    assert len(result) == 2
    names = {r.name for r in result}
    assert names == {"李明", "小雨"}


def test_merge_roles_update_existing():
    existing = [Role(name="李明", gender="unknown")]
    new = [{"name": "李明", "gender": "male", "age": "adult", "aliases": ["小李"]}]
    result = _merge_roles(existing, new)
    assert len(result) == 1
    assert result[0].gender == "male"
    assert result[0].age == "adult"
    assert "小李" in result[0].aliases


def test_split_long_text_short():
    text = "短文本"
    assert _split_long_text(text) == ["短文本"]


def test_split_long_text_long():
    # Create text exceeding MAX_CHUNK_CHARS
    para = "这是一段测试文本。" * 100  # ~900 chars
    text = "\n".join([para] * 20)  # ~18000 chars
    chunks = _split_long_text(text, max_chars=5000)
    assert len(chunks) > 1
    # Each chunk should be under the limit (approx)
    for c in chunks:
        assert len(c) < 6000  # allow some slack for paragraph boundaries
