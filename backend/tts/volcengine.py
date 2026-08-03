"""Volcengine (ByteDance) TTS provider — 豆包 TTS via WebSocket.

Docs: https://www.volcengine.com/docs/6561/79817

Authentication: App ID + Access Token.
Voice cloning: seed-icl-2.0 (Resource-Id header).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid
from pathlib import Path
from urllib.parse import quote

from tts.base import TTSProvider, VoiceConfig

VOLCENGINE_WSS = (
    "wss://openspeech.bytedance.com/api/v3/tts/bidirection"
)


class VolcengineTTSProvider(TTSProvider):
    engine_id = "volcengine"

    """火山引擎豆包 TTS V3 双向流式."""

    def __init__(self, app_id: str = "", access_token: str = ""):
        self.app_id = app_id
        self.access_token = access_token

    def _build_auth_query(self) -> str:
        """Build the auth query string for the WebSocket URL."""
        timestamp = int(time.time())
        expired = timestamp + 86400

        raw = (
            f"app_id={self.app_id}&"
            f"timestamp={timestamp}&"
            f"expired={expired}"
        )
        signature = hmac.new(
            self.access_token.encode("utf-8"),
            raw.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return (
            f"app_id={self.app_id}"
            f"&timestamp={timestamp}"
            f"&expired={expired}"
            f"&signature={signature}"
        )

    async def synthesize(self, text: str, voice: VoiceConfig, output_path: Path) -> Path:
        if not self.app_id or not self.access_token:
            raise ValueError("Volcengine app_id and access_token are required")

        voice_type = voice.voice_id or "zh_female_qingxin"
        model = "seed-tts-edm"
        encoding = "pcm"
        rate = voice.speed

        import websockets

        # Cloning: use resource header for seed-icl-2.0
        headers = {}
        if voice.reference_audio:
            headers["Resource-Id"] = "volc.service_type.10029"  # seed-icl-2.0

        url = f"{VOLCENGINE_WSS}?{self._build_auth_query()}"

        event_id = str(uuid.uuid4())
        start_msg = {
            "event": event_id,
            "header": {
                "namespace": "BidirectionalTTS",
                "name": "StartConnection",
                "app_id": self.app_id,
            },
            "payload": {
                "tts_request": {
                    "model_params": {
                        "model": model,
                    },
                    "audio_params": {
                        "format": encoding,
                        "sample_rate": 24000,
                        "speed_ratio": rate,
                    },
                    "speaker": {"voice_type": voice_type},
                }
            },
        }

        # If cloning, add reference audio
        if voice.reference_audio:
            ref_bytes = Path(voice.reference_audio).read_bytes() if Path(voice.reference_audio).exists() else None
            if ref_bytes:
                start_msg["payload"]["tts_request"]["speaker"]["reference_audio"] = base64.b64encode(ref_bytes).decode()

        task_msg = {
            "event": str(uuid.uuid4()),
            "header": {
                "namespace": "BidirectionalTTS",
                "name": "StartTask",
                "app_id": self.app_id,
            },
            "payload": {
                "text": text,
            },
        }

        audio_chunks: list[bytes] = []

        async with websockets.connect(url, additional_headers=headers) as ws:
            await ws.send(json.dumps(start_msg))
            await ws.send(json.dumps(task_msg))

            # Send finish signal
            finish_msg = {
                "event": str(uuid.uuid4()),
                "header": {"namespace": "BidirectionalTTS", "name": "FinishTask", "app_id": self.app_id},
                "payload": {},
            }
            await ws.send(json.dumps(finish_msg))

            while True:
                msg = await ws.recv()
                data = json.loads(msg) if isinstance(msg, str) else None
                if data:
                    name = data.get("header", {}).get("name", "")
                    if "Error" in name or "Failed" in name:
                        raise RuntimeError(f"Volcengine error: {data}")
                    if name == "TaskFinished":
                        break
                else:
                    audio_chunks.append(msg)

        output_path.write_bytes(b"".join(audio_chunks))
        return output_path

    def is_available(self) -> bool:
        return bool(self.app_id and self.access_token)
