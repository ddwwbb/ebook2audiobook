"""Shared base for local TTS engines that expose an HTTP API.

Most local TTS engines (GPT-SoVITS, CosyVoice, IndexTTS, Fish Speech, F5-TTS,
ChatTTS) run as separate HTTP services. This base class handles the common
HTTP POST pattern: send text + reference audio, receive audio bytes.
"""

from __future__ import annotations

import base64
from pathlib import Path

import httpx

from tts.base import TTSProvider, VoiceConfig


class HTTPLocalTTSProvider(TTSProvider):
    """Base for local TTS engines with an HTTP API.

    Subclasses define:
    - endpoint: the API URL path (e.g. /tts, /synthesize)
    - build_payload(): construct the request body from text + voice config
    - parse_response(): extract audio bytes from the response
    """

    base_url: str = ""  # e.g. http://127.0.0.1:9880
    endpoint: str = ""

    def __init__(self, base_url: str = ""):
        if base_url:
            self.base_url = base_url.rstrip("/")

    def url(self) -> str:
        return f"{self.base_url}{self.endpoint}"

    def build_payload(self, text: str, voice: VoiceConfig) -> dict:
        raise NotImplementedError

    def parse_response(self, data: bytes | dict) -> bytes:
        """Extract raw audio bytes from response."""
        if isinstance(data, bytes):
            return data
        # If JSON with base64 audio
        for key in ("audio", "data", "wav"):
            if key in data:
                val = data[key]
                if isinstance(val, str):
                    return base64.b64decode(val)
                return val
        raise ValueError(f"Cannot extract audio from response: {data}")

    async def synthesize(self, text: str, voice: VoiceConfig, output_path: Path) -> Path:
        if not self.base_url:
            raise ValueError(f"{self.engine_id} base_url not configured")

        payload = self.build_payload(text, voice)
        async with httpx.AsyncClient(timeout=300) as client:
            # Try JSON first, fall back to raw response
            resp = await client.post(self.url(), json=payload)

            content_type = resp.headers.get("content-type", "")
            if "application/json" in content_type:
                audio_bytes = self.parse_response(resp.json())
            elif "audio" in content_type or "octet-stream" in content_type:
                audio_bytes = resp.content
            else:
                # Try to parse as JSON, fall back to raw bytes
                try:
                    audio_bytes = self.parse_response(resp.json())
                except Exception:
                    audio_bytes = resp.content

        output_path.write_bytes(audio_bytes)
        return output_path

    def _encode_ref(self, ref_path: str) -> str:
        """Read reference audio file and return base64."""
        p = Path(ref_path)
        if not p.exists():
            raise FileNotFoundError(f"Reference audio not found: {ref_path}")
        return base64.b64encode(p.read_bytes()).decode("utf-8")

    def is_available(self) -> bool:
        return bool(self.base_url)
