"""CosyVoice 2 local provider — via FastAPI server (model inference API).

CosyVoice 2 repo ships a webui/api_server.py that exposes:
- POST /api/tts — text → audio with optional reference for zero-shot cloning

Repo: https://github.com/FunAudioLLM/CosyVoice
License: Apache-2.0
"""

from __future__ import annotations

from tts.base import VoiceConfig
from tts.http_local import HTTPLocalTTSProvider


class CosyVoiceLocalProvider(HTTPLocalTTSProvider):
    engine_id = "cosyvoice_local"

    """CosyVoice 2 local inference server."""

    endpoint = "/api/tts"

    def build_payload(self, text: str, voice: VoiceConfig) -> dict:
        payload: dict = {
            "text": text,
            "voice": voice.voice_id or "中文女",
            "speed": voice.speed,
        }
        # Zero-shot cloning: pass reference audio as base64
        if voice.reference_audio:
            payload["reference_audio"] = self._encode_ref(voice.reference_audio)
        return payload
