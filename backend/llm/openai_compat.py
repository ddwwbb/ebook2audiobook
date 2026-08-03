"""OpenAI-compatible LLM client.

Covers: OpenAI, DeepSeek, Qwen (DashScope OpenAI mode), GLM, Kimi, Ollama, vLLM, etc.
Endpoint: POST {base_url}/chat/completions
"""

from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from llm.client import LLMClient, LLMConfig, LLMMessage


class OpenAICompatClient(LLMClient):
    """Client for any OpenAI-compatible API."""

    def _headers(self, config: LLMConfig) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if config.api_key:
            h["Authorization"] = f"Bearer {config.api_key}"
        return h

    def _payload(
        self, messages: list[LLMMessage], config: LLMConfig, *, stream: bool, json_mode: bool
    ) -> dict:
        payload: dict = {
            "model": config.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "stream": stream,
        }
        if json_mode and config.enable_json:
            payload["response_format"] = {"type": "json_object"}
        return payload

    def _url(self, config: LLMConfig) -> str:
        base = config.base_url.rstrip("/")
        return f"{base}/chat/completions"

    async def complete(self, messages: list[LLMMessage], config: LLMConfig) -> str:
        """Non-streaming completion."""
        payload = self._payload(messages, config, stream=False, json_mode=False)
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                self._url(config), headers=self._headers(config), json=payload
            )
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"]

    async def complete_json(self, messages: list[LLMMessage], config: LLMConfig) -> str:
        """Non-streaming completion with JSON response format."""
        payload = self._payload(messages, config, stream=False, json_mode=True)
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                self._url(config), headers=self._headers(config), json=payload
            )
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"]

    async def stream(
        self, messages: list[LLMMessage], config: LLMConfig
    ) -> AsyncIterator[str]:
        """Streaming completion via SSE."""
        payload = self._payload(messages, config, stream=True, json_mode=False)
        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream(
                "POST", self._url(config), headers=self._headers(config), json=payload
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0]["delta"].get("content")
                        if delta:
                            yield delta
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
