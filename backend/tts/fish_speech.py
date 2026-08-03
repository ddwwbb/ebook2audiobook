"""Fish Speech local provider — Fish Audio's open-source TTS.

Repo: https://github.com/fishaudio/fish-speech
License: FISH AUDIO RESEARCH LICENSE (commercial use requires evaluation)
Default API server port: 8080

Fish Speech uses a Dual-AR architecture. API exposes:
- POST /v1/tts — text + reference → audio
"""

from __future__ import annotations

from tts.base import VoiceConfig
from tts.http_local import HTTPLocalTTSProvider


class FishSpeechProvider(HTTPLocalTTSProvider):
    engine_id = "fish_speech"

    """Fish Speech local inference server."""

    endpoint = "/v1/tts"

    def build_payload(self, text: str, voice: VoiceConfig) -> dict:
        payload: dict = {
            "text": text,
            "format": "wav",
            "speed": voice.speed,
        }
        # Zero-shot cloning via reference audio
        if voice.reference_audio:
            payload["reference_audio"] = self._encode_ref(voice.reference_audio)
        if voice.voice_id:
            # Can also use a predefined voice ID instead of reference audio
            payload["voice_id"] = voice.voice_id
        return payload
