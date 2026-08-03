"""Xiaomi MiMo TTS provider — voice cloning via OpenAI-compatible API.

Model: mimo-v2.5-tts-voiceclone
Protocol: POST /v1/chat/completions with audio.voice = base64 reference audio.
Reference: xiaozhi-esp32-server-java MimoVoiceCloneProvider.java

This provider does zero-shot voice cloning: give a reference audio,
it synthesizes new text in that voice. Each character can have its own
reference audio.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

import httpx

from tts.base import TTSProvider, VoiceConfig


class MimoTTSProvider(TTSProvider):
    engine_id = "mimo"

    """小米 MiMo TTS — OpenAI-compatible voice cloning."""

    def __init__(self, base_url: str = "", api_key: str = ""):
        # base_url example: https://api.mimo.xiaomi.com
        self.base_url = base_url.rstrip("/") if base_url else "https://api.mimo.xiaomi.com"
        self.api_key = api_key

    def _load_reference_base64(self, ref_path: str) -> str:
        """Load reference audio file and encode as base64."""
        p = Path(ref_path)
        if not p.exists():
            raise FileNotFoundError(f"Reference audio not found: {ref_path}")
        return base64.b64encode(p.read_bytes()).decode("utf-8")

    async def synthesize(self, text: str, voice: VoiceConfig, output_path: Path) -> Path:
        if not self.api_key:
            raise ValueError("MiMo API key is required")
        if not voice.reference_audio:
            raise ValueError("MiMo requires reference_audio for voice cloning")

        ref_b64 = self._load_reference_base64(voice.reference_audio)

        # OpenAI-compatible chat/completions with audio.voice field
        # The reference audio is embedded in the "audio" param
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": voice.voice_id or "mimo-v2.5-tts-voiceclone",
            "messages": [
                {
                    "role": "user",
                    "content": text,
                }
            ],
            "audio": {
                "voice": ref_b64,
                "format": "wav",
            },
        }

        # Extra params (speed, pitch) via extra body
        if voice.speed != 1.0:
            payload["audio"]["speed"] = voice.speed
        if voice.pitch != 0.0:
            payload["audio"]["pitch"] = voice.pitch

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        # Response may contain base64 audio in choices[0].message.audio.data
        # or as a URL. Handle both.
        message = data.get("choices", [{}])[0].get("message", {})
        audio_info = message.get("audio", {})

        if audio_info.get("data"):
            # base64-encoded audio
            audio_bytes = base64.b64decode(audio_info["data"])
            output_path.write_bytes(audio_bytes)
        elif audio_info.get("url"):
            # URL to audio file
            async with httpx.AsyncClient() as client:
                audio_resp = await client.get(audio_info["url"])
                audio_resp.raise_for_status()
                output_path.write_bytes(audio_resp.content)
        else:
            raise RuntimeError(f"MiMo response missing audio data: {data}")

        return output_path

    def is_available(self) -> bool:
        return bool(self.api_key)
