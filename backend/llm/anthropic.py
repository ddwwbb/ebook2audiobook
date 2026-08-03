"""Anthropic Claude LLM client (native Messages API).

Endpoint: POST {base_url}/v1/messages
SSE stream events: message_start, content_block_delta, message_stop
"""

from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from llm.client import LLMClient, LLMConfig, LLMMessage


class AnthropicClient(LLMClient):
    """Client for Anthropic Claude Messages API."""

    API_VERSION = "2023-06-01"

    def _headers(self, config: LLMConfig) -> dict[str, str]:
        return {
            "x-api-key": config.api_key,
            "anthropic-version": self.API_VERSION,
            "Content-Type": "application/json",
        }

    def _split_system(self, messages: list[LLMMessage]) -> tuple[str | None, list[dict]]:
        """Claude expects system as a top-level param, not in messages."""
        system_text = None
        chat_msgs = []
        for m in messages:
            if m.role == "system":
                system_text = m.content
            else:
                chat_msgs.append({"role": m.role, "content": m.content})
        return system_text, chat_msgs

    def _payload(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
        *,
        stream: bool,
    ) -> dict:
        system_text, chat_msgs = self._split_system(messages)
        payload: dict = {
            "model": config.model,
            "messages": chat_msgs,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "stream": stream,
        }
        if system_text:
            payload["system"] = system_text
        return payload

    def _url(self, config: LLMConfig) -> str:
        base = config.base_url.rstrip("/")
        # Support both full and partial base URLs
        if base.endswith("/v1"):
            return f"{base}/messages"
        return f"{base}/v1/messages"

    async def complete(self, messages: list[LLMMessage], config: LLMConfig) -> str:
        payload = self._payload(messages, config, stream=False)
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                self._url(config), headers=self._headers(config), json=payload
            )
            resp.raise_for_status()
            data = resp.json()
        # Extract text from content blocks
        parts = [
            block["text"] for block in data.get("content", []) if block.get("type") == "text"
        ]
        return "".join(parts)

    async def complete_json(self, messages: list[LLMMessage], config: LLMConfig) -> str:
        """Claude doesn't have response_format; rely on prompt + extract JSON from text."""
        text = await self.complete(messages, config)
        return text

    async def stream(
        self, messages: list[LLMMessage], config: LLMConfig
    ) -> AsyncIterator[str]:
        payload = self._payload(messages, config, stream=True)
        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream(
                "POST", self._url(config), headers=self._headers(config), json=payload
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    try:
                        event = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    if event.get("type") == "content_block_delta":
                        delta = event.get("delta", {})
                        if delta.get("type") == "text_delta":
                            text = delta.get("text")
                            if text:
                                yield text
