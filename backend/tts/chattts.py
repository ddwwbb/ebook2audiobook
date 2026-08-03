"""ChatTTS local provider — 2noise's conversational TTS.

Repo: https://github.com/2noise/ChatTTS
License: Code AGPL-3.0; model CC-BY-NC (non-commercial only)
Default: API server

ChatTTS does NOT support zero-shot cloning. Uses random speaker sampling
or fixed seed-based speaker selection.
"""

from __future__ import annotations

import random

from tts.base import VoiceConfig
from tts.http_local import HTTPLocalTTSProvider


class ChatTTSProvider(HTTPLocalTTSProvider):
    engine_id = "chattts"

    """ChatTTS local inference server."""

    endpoint = "/generate_audio"

    def build_payload(self, text: str, voice: VoiceConfig) -> dict:
        # ChatTTS uses speaker seed, not reference audio
        # voice_id can be a numeric seed
        seed = int(voice.voice_id) if voice.voice_id and voice.voice_id.isdigit() else random.randint(0, 2222)
        return {
            "text": text,
            "speaker_seed": seed,
            "speed": voice.speed,
        }
