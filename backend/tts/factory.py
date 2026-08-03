"""TTS provider factory — create provider instances from engine id + config."""

from __future__ import annotations

from typing import Any

from tts.base import TTSProvider

# Single source of truth for engine metadata (Fix #10).
# Consumed by routes_voices.py API and indirectly by the frontend.
ENGINE_METADATA: list[dict[str, Any]] = [
    {"id": "edge", "name": "Edge TTS", "type": "cloud", "cloning": False, "license": "free"},
    {"id": "dashscope", "name": "阿里 CosyVoice", "type": "cloud", "cloning": True, "license": "commercial"},
    {"id": "volcengine", "name": "火山豆包 TTS", "type": "cloud", "cloning": True, "license": "commercial"},
    {"id": "mimo", "name": "小米 MiMo", "type": "cloud", "cloning": True, "license": "commercial"},
    {"id": "cosyvoice_local", "name": "CosyVoice 2 (本地)", "type": "local", "cloning": True, "license": "Apache-2.0"},
    {"id": "gpt_sovits", "name": "GPT-SoVITS V4 (本地)", "type": "local", "cloning": True, "license": "MIT"},
    {"id": "indextts", "name": "IndexTTS 2 (本地)", "type": "local", "cloning": True, "license": "bilibili"},
    {"id": "fish_speech", "name": "Fish Speech (本地)", "type": "local", "cloning": True, "license": "Fish License"},
    {"id": "f5_tts", "name": "F5-TTS (本地)", "type": "local", "cloning": True, "license": "CC-BY-NC"},
    {"id": "chattts", "name": "ChatTTS (本地)", "type": "local", "cloning": False, "license": "CC-BY-NC"},
    {"id": "sherpa_vits", "name": "sherpa-onnx VITS", "type": "local", "cloning": False, "license": "Apache-2.0"},
    {"id": "sherpa_kokoro", "name": "sherpa-onnx Kokoro", "type": "local", "cloning": False, "license": "Apache-2.0"},
]

# Config fields each engine needs (for Settings UI rendering)
ENGINE_CONFIG_FIELDS: dict[str, list[dict[str, str]]] = {
    "edge": [],
    "dashscope": [{"key": "api_key", "label": "DashScope API Key", "type": "password"}],
    "volcengine": [
        {"key": "app_id", "label": "App ID", "type": "text"},
        {"key": "access_token", "label": "Access Token", "type": "password"},
    ],
    "mimo": [
        {"key": "base_url", "label": "Base URL", "type": "text"},
        {"key": "api_key", "label": "API Key", "type": "password"},
    ],
    "cosyvoice_local": [{"key": "base_url", "label": "服务地址", "type": "text"}],
    "gpt_sovits": [{"key": "base_url", "label": "服务地址", "type": "text"}],
    "indextts": [{"key": "base_url", "label": "服务地址", "type": "text"}],
    "fish_speech": [{"key": "base_url", "label": "服务地址", "type": "text"}],
    "f5_tts": [{"key": "base_url", "label": "服务地址", "type": "text"}],
    "chattts": [{"key": "base_url", "label": "服务地址", "type": "text"}],
    "sherpa_vits": [{"key": "model_dir", "label": "模型目录", "type": "text"}],
    "sherpa_kokoro": [{"key": "model_dir", "label": "模型目录", "type": "text"}],
}


def create_tts_provider(engine_id: str, **config: Any) -> TTSProvider:
    """Create a TTS provider instance by engine id.

    Cloud engines:
    - edge: no config needed
    - dashscope: api_key
    - volcengine: app_id, access_token
    - mimo: base_url, api_key

    Local engines (HTTP API servers):
    - cosyvoice_local: base_url
    - gpt_sovits: base_url
    - indextts: base_url
    - fish_speech: base_url
    - f5_tts: base_url
    - chattts: base_url

    Local engines (ONNX inference):
    - sherpa_vits: model_dir
    - sherpa_kokoro: model_dir
    """
    # === Cloud ===
    if engine_id == "edge":
        from tts.edge import EdgeTTSProvider
        return EdgeTTSProvider()

    if engine_id == "dashscope":
        from tts.dashscope import DashscopeTTSProvider
        return DashscopeTTSProvider(api_key=config.get("api_key", ""))

    if engine_id == "volcengine":
        from tts.volcengine import VolcengineTTSProvider
        return VolcengineTTSProvider(
            app_id=config.get("app_id", ""),
            access_token=config.get("access_token", ""),
        )

    if engine_id == "mimo":
        from tts.mimo import MimoTTSProvider
        return MimoTTSProvider(
            base_url=config.get("base_url", ""),
            api_key=config.get("api_key", ""),
        )

    # === Local HTTP API ===
    if engine_id == "cosyvoice_local":
        from tts.cosyvoice_local import CosyVoiceLocalProvider
        return CosyVoiceLocalProvider(base_url=config.get("base_url", ""))

    if engine_id == "gpt_sovits":
        from tts.gpt_sovits import GPTSoVITSProvider
        return GPTSoVITSProvider(base_url=config.get("base_url", ""))

    if engine_id == "indextts":
        from tts.indextts import IndexTTSProvider
        return IndexTTSProvider(base_url=config.get("base_url", ""))

    if engine_id == "fish_speech":
        from tts.fish_speech import FishSpeechProvider
        return FishSpeechProvider(base_url=config.get("base_url", ""))

    if engine_id == "f5_tts":
        from tts.f5_tts import F5TTSProvider
        return F5TTSProvider(base_url=config.get("base_url", ""))

    if engine_id == "chattts":
        from tts.chattts import ChatTTSProvider
        return ChatTTSProvider(base_url=config.get("base_url", ""))

    # === Local ONNX ===
    if engine_id == "sherpa_vits":
        from tts.sherpa_vits import SherpaVITSProvider
        return SherpaVITSProvider(
            model_dir=config.get("model_dir", ""),
            model_type="vits",
        )

    if engine_id == "sherpa_kokoro":
        from tts.sherpa_kokoro import SherpaKokoroProvider
        return SherpaKokoroProvider(
            model_dir=config.get("model_dir", ""),
        )

    raise ValueError(f"Unknown TTS engine: {engine_id}")
