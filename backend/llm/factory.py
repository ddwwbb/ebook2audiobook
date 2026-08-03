"""LLM client factory — instantiate client by provider type."""

from __future__ import annotations

import json
import re

from llm.anthropic import AnthropicClient
from llm.client import LLMClient, LLMConfig
from llm.openai_compat import OpenAICompatClient


def create_client(config: LLMConfig) -> LLMClient:
    """Return the appropriate LLM client based on config.provider."""
    if config.provider == "anthropic":
        return AnthropicClient()
    if config.provider == "openai_compat":
        return OpenAICompatClient()
    raise ValueError(
        f"Unknown LLM provider: {config.provider}. "
        f"Supported: openai_compat, anthropic"
    )


def extract_json(text: str) -> dict | list | None:
    """Best-effort extract JSON object/array from LLM text output.

    Handles ```json fences, leading/trailing prose, and partial outputs.
    """
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        pass

    # Try json fence
    fence = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if fence:
        try:
            return json.loads(fence.group(1).strip())
        except (ValueError, TypeError):
            pass

    # Try finding first { or [ to last } or ]
    for open_ch, close_ch in [("{", "}"), ("[", "]")]:
        start = text.find(open_ch)
        end = text.rfind(close_ch)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except (ValueError, TypeError):
                pass

    return None
