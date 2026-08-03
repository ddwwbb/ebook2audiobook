"""Abstract LLM client interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Literal


@dataclass
class LLMConfig:
    provider: Literal["openai_compat", "anthropic"]
    base_url: str
    api_key: str
    model: str
    temperature: float = 0.3
    max_tokens: int = 4096
    enable_json: bool = True


@dataclass
class LLMMessage:
    role: Literal["system", "user", "assistant"]
    content: str


class LLMClient(ABC):
    """All LLM providers implement this."""

    @abstractmethod
    async def complete(self, messages: list[LLMMessage], config: LLMConfig) -> str:
        """Non-streaming completion. Returns full text."""
        ...

    @abstractmethod
    async def stream(
        self, messages: list[LLMMessage], config: LLMConfig
    ) -> AsyncIterator[str]:
        """Streaming completion. Yields text chunks."""
        ...

    async def complete_json(self, messages: list[LLMMessage], config: LLMConfig) -> str:
        """Completion with JSON response format hint. Default delegates to complete()."""
        return await self.complete(messages, config)
