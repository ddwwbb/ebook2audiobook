"""Alibaba DashScope TTS provider — CosyVoice / Qwen3-TTS via WebSocket V3.

Docs: https://help.aliyun.com/zh/model-studio/developer-reference/cosyvoice

Authentication: API key (DashScope API key).
Voice cloning: CosyVoice supports voice cloning via voice prefix (cosyvoice_clone_xxx).
"""

from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path

from tts.base import TTSProvider, VoiceConfig

DASHSCOPE_WSS = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"


class DashscopeTTSProvider(TTSProvider):
    engine_id = "dashscope"

    """阿里云 DashScope CosyVoice / Qwen3-TTS."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    async def synthesize(self, text: str, voice: VoiceConfig, output_path: Path) -> Path:
        if not self.api_key:
            raise ValueError("DashScope API key is required")

        voice_id = voice.voice_id or "cosyvoice-v2-longxiaochun"
        model = "cosyvoice-v2"

        # CosyVoice clone: if reference audio is provided, use it for zero-shot cloning
        # voice_id should be prefixed with "cosyvoice_clone_" for cloned voices
        if voice.reference_audio and not voice_id.startswith("cosyvoice_clone_"):
            voice_id = "cosyvoice_clone_v2"

        task_id = str(uuid.uuid4())

        import websockets

        headers = {
            "Authorization": f"bearer {self.api_key}",
            "X-DashScope-DataInspection": "enable",
        }

        # Run payload: streaming synthesis
        run_task = {
            "header": {
                "action": "run-task",
                "task_id": task_id,
                "streaming": "duplex",
            },
            "payload": {
                "task_group": "audio",
                "task": "tts",
                "function": "SpeechSynthesizer",
                "model": model,
                "parameters": {
                    "voice": voice_id,
                    "format": "pcm",
                    "sample_rate": 22050,
                    "rate": voice.speed,
                    "pitch": voice.pitch,
                },
                "input": {"text": text},
            },
        }

        # For cloning, add reference audio URL to parameters
        if voice.reference_audio:
            run_task["payload"]["parameters"]["reference_audio"] = voice.reference_audio

        audio_chunks: list[bytes] = []

        async with websockets.connect(DASHSCOPE_WSS, additional_headers=headers) as ws:
            await ws.send(json.dumps(run_task))

            while True:
                msg = await ws.recv()
                if isinstance(msg, str):
                    data = json.loads(msg)
                    header = data.get("header", {})
                    event = header.get("event")
                    if event == "task-failed":
                        raise RuntimeError(f"DashScope task failed: {data}")
                    if event == "task-finished":
                        break
                else:
                    audio_chunks.append(msg)

        # Write raw PCM; caller (merger) will handle conversion via ffmpeg
        output_path.write_bytes(b"".join(audio_chunks))
        return output_path

    def is_available(self) -> bool:
        return bool(self.api_key)
