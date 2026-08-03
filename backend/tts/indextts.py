"""IndexTTS 2 local provider — bilibili's open-source TTS.

Repo: https://github.com/index-tts/index-tts
License: bilibili Model Use License (check terms for commercial use)
Default: runs as Gradio/API server

IndexTTS 2 supports emotion decoupling — reference audio controls voice,
and a separate emotion reference can control the emotion.
"""

from __future__ import annotations

from tts.base import VoiceConfig
from tts.http_local import HTTPLocalTTSProvider


class IndexTTSProvider(HTTPLocalTTSProvider):
    engine_id = "indextts"

    """IndexTTS 2 local inference server."""

    endpoint = "/synthesize"

    def build_payload(self, text: str, voice: VoiceConfig) -> dict:
        payload: dict = {
            "text": text,
            "speed": voice.speed,
        }
        # Zero-shot cloning: reference audio as base64 or path
        if voice.reference_audio:
            payload["audio_prompt"] = self._encode_ref(voice.reference_audio)
        if voice.extra.get("emotion_ref"):
            # IndexTTS 2 emotion decoupling
            payload["emotion_prompt"] = voice.extra["emotion_ref"]
        return payload
