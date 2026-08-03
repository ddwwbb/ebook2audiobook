"""Edge TTS provider — free Microsoft Edge TTS, zero config.

Uses the edge-tts library. Good default voice for Chinese: zh-CN-XiaoyiNeural.
"""

from __future__ import annotations

from pathlib import Path

import edge_tts

from tts.base import TTSProvider, VoiceConfig

# Common Chinese voices
ZH_VOICES = {
    "female_xiaoyi": "zh-CN-XiaoyiNeural",
    "female_xiaoxiao": "zh-CN-XiaoxiaoNeural",
    "female_xiaohan": "zh-CN-XiaohanNeural",
    "female_xiaomeng": "zh-CN-XiaomengNeural",
    "female_xiaoqiu": "zh-CN-XiaoqiuNeural",
    "female_xiaorui": "zh-CN-XiaoruiNeural",
    "female_xiaoshuang": "zh-CN-XiaoshuangNeural",
    "female_xiaochen": "zh-CN-XiaochenNeural",
    "female_xiaohui": "zh-CN-XiaohuiNeural",
    "male_yunyang": "zh-CN-YunyangNeural",
    "male_yunxi": "zh-CN-YunxiNeural",
    "male_yunjian": "zh-CN-YunjianNeural",
    "male_yunfeng": "zh-CN-YunfengNeural",
}


class EdgeTTSProvider(TTSProvider):
    engine_id = "edge"

    """Microsoft Edge TTS — free, no API key needed."""

    async def synthesize(self, text: str, voice: VoiceConfig, output_path: Path) -> Path:
        voice_name = voice.voice_id or "zh-CN-XiaoyiNeural"

        # Allow shorthand keys like "female_xiaoyi"
        if voice_name in ZH_VOICES:
            voice_name = ZH_VOICES[voice_name]

        rate_pct = int((voice.speed - 1.0) * 100)
        pitch_hz = int(voice.pitch * 100)
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice_name,
            rate=f"{rate_pct:+d}%",
            pitch=f"{pitch_hz:+d}Hz",
        )
        await communicate.save(str(output_path))
        return output_path

    def is_available(self) -> bool:
        return True
