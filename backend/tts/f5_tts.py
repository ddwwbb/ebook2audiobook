"""F5-TTS local provider — SWivid's flow-matching TTS.

Repo: https://github.com/SWivid/F5-TTS
License: Code MIT; weights CC-BY-NC (non-commercial only)
Default: Gradio/API server

F5-TTS supports zero-shot cloning with reference audio + reference text.
"""

from __future__ import annotations

from tts.base import VoiceConfig
from tts.http_local import HTTPLocalTTSProvider


class F5TTSProvider(HTTPLocalTTSProvider):
    engine_id = "f5_tts"

    """F5-TTS local inference server."""

    endpoint = "/synth"

    def build_payload(self, text: str, voice: VoiceConfig) -> dict:
        payload: dict = {
            "text": text,
            "speed": voice.speed,
        }
        # F5-TTS needs reference audio + reference text for cloning
        if voice.reference_audio:
            payload["ref_audio"] = self._encode_ref(voice.reference_audio)
            # voice_id format: "ref_text" or "ref_text:other_config"
            payload["ref_text"] = voice.voice_id or ""
        return payload
