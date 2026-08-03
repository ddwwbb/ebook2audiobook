"""Tests for LLM client factory and JSON extraction."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from llm.anthropic import AnthropicClient
from llm.client import LLMConfig
from llm.factory import create_client, extract_json
from llm.openai_compat import OpenAICompatClient


def test_factory_openai():
    cfg = LLMConfig(
        provider="openai_compat",
        base_url="https://api.deepseek.com/v1",
        api_key="sk-test",
        model="deepseek-chat",
    )
    client = create_client(cfg)
    assert isinstance(client, OpenAICompatClient)


def test_factory_anthropic():
    cfg = LLMConfig(
        provider="anthropic",
        base_url="https://api.anthropic.com",
        api_key="sk-ant-test",
        model="claude-sonnet-4-5-20250514",
    )
    client = create_client(cfg)
    assert isinstance(client, AnthropicClient)


def test_factory_unknown():
    import pytest

    cfg = LLMConfig(
        provider="unknown",
        base_url="http://localhost",
        api_key="",
        model="x",
    )
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        create_client(cfg)


def test_openai_url():
    cfg = LLMConfig(
        provider="openai_compat",
        base_url="https://api.deepseek.com/v1",
        api_key="k",
        model="m",
    )
    client = OpenAICompatClient()
    assert client._url(cfg) == "https://api.deepseek.com/v1/chat/completions"


def test_anthropic_url():
    cfg = LLMConfig(
        provider="anthropic",
        base_url="https://api.anthropic.com",
        api_key="k",
        model="m",
    )
    client = AnthropicClient()
    assert client._url(cfg) == "https://api.anthropic.com/v1/messages"


def test_anthropic_url_with_v1():
    cfg = LLMConfig(
        provider="anthropic",
        base_url="https://api.anthropic.com/v1",
        api_key="k",
        model="m",
    )
    client = AnthropicClient()
    assert client._url(cfg) == "https://api.anthropic.com/v1/messages"


def test_anthropic_system_split():
    from llm.client import LLMMessage

    client = AnthropicClient()
    messages = [
        LLMMessage(role="system", content="你是助手"),
        LLMMessage(role="user", content="你好"),
        LLMMessage(role="assistant", content="你好！"),
    ]
    system, chat = client._split_system(messages)
    assert system == "你是助手"
    assert len(chat) == 2
    assert chat[0]["role"] == "user"
    assert chat[1]["role"] == "assistant"


def test_extract_json_direct():
    assert extract_json('{"a": 1}') == {"a": 1}
    assert extract_json("[1, 2, 3]") == [1, 2, 3]


def test_extract_json_fenced():
    text = '结果如下：\n```json\n{"name": "李明", "age": 25}\n```\n以上'
    result = extract_json(text)
    assert result == {"name": "李明", "age": 25}


def test_extract_json_with_prose():
    text = '根据分析，角色信息为 {"name": "小雨", "gender": "female"} 希望有帮助'
    result = extract_json(text)
    assert result == {"name": "小雨", "gender": "female"}


def test_extract_json_invalid():
    assert extract_json("这不是 JSON") is None
    assert extract_json("") is None
