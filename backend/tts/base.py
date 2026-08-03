"""TTS provider abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class VoiceConfig:
    """Voice configuration for a single character/role."""

    engine: str
    voice_id: str = ""
    reference_audio: str | None = None  # path or base64, for cloning engines
    pitch: float = 0.0
    speed: float = 1.0
    extra: dict[str, Any] = field(default_factory=dict)


class TTSProvider(ABC):
    """All TTS engines implement this interface."""

    engine_id: str = ""

    @abstractmethod
    async def synthesize(self, text: str, voice: VoiceConfig, output_path: Path) -> Path:
        """Synthesize text to an audio file. Returns the output path."""
        ...

    def is_available(self) -> bool:
        """Check if the engine is ready (models loaded, API key set, etc.)."""
        return True
