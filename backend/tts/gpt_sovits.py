"""GPT-SoVITS V4 local provider — via API server.

GPT-SoVITS repo ships api_v2.py (api.py for v1) exposing:
- POST /tts — text + reference audio → audio

Repo: https://github.com/RVC-Boss/GPT-SoVITS
License: MIT
Default port: 9880
"""

from __future__ import annotations

from tts.base import VoiceConfig
from tts.http_local import HTTPLocalTTSProvider


class GPTSoVITSProvider(HTTPLocalTTSProvider):
    engine_id = "gpt_sovits"

    """GPT-SoVITS V4 local inference server."""

    endpoint = "/tts"

    def build_payload(self, text: str, voice: VoiceConfig) -> dict:
        payload: dict = {
            "text": text,
            "text_language": "zh",
            "speed": voice.speed,
        }
        # GPT-SoVITS requires reference audio for cloning
        # voice_id format: "ref_wav_path:prompt_text:prompt_language"
        if voice.reference_audio:
            parts = voice.voice_id.split(":") if voice.voice_id else []
            payload["refer_wav_path"] = voice.reference_audio
            payload["prompt_text"] = parts[1] if len(parts) > 1 else ""
            payload["prompt_language"] = parts[2] if len(parts) > 2 else "zh"
        elif ":" in (voice.voice_id or ""):
            parts = voice.voice_id.split(":")
            payload["refer_wav_path"] = parts[0]
            payload["prompt_text"] = parts[1] if len(parts) > 1 else ""
            payload["prompt_language"] = parts[2] if len(parts) > 2 else "zh"
        return payload
