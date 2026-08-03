"""sherpa-onnx VITS provider — local ONNX inference for VITS models.

Supports Chinese VITS models (e.g. MeloTTS-ZH, WangyeZJW).
Uses sherpa-onnx Python API for offline inference.

Repo: https://github.com/k2-fsa/sherpa-onnx
License: Apache-2.0
Runs on CPU/ARM (including RK3588 with RKNN).
"""

from __future__ import annotations

import logging
from pathlib import Path

from tts.base import TTSProvider, VoiceConfig

logger = logging.getLogger(__name__)

# Lazily imported; sherpa-onnx is a heavy native dependency
_sherpa = None


def _import_sherpa():
    global _sherpa
    if _sherpa is None:
        try:
            import sherpa_onnx
            _sherpa = sherpa_onnx
        except ImportError:
            raise ImportError(
                "sherpa-onnx not installed. Install with: pip install sherpa-onnx"
            )
    return _sherpa


class SherpaVITSProvider(TTSProvider):
    engine_id = "sherpa_vits"

    """sherpa-onnx VITS — local ONNX inference, CPU/ARM friendly."""

    def __init__(self, model_dir: str = "", model_type: str = "vits"):
        self.model_dir = model_dir
        self.model_type = model_type
        self._generator = None

    def _get_generator(self):
        if self._generator is None:
            sherpa = _import_sherpa()
            model_path = str(Path(self.model_dir) / "model.onnx")
            tokens_path = str(Path(self.model_dir) / "tokens.txt")
            lexicon_path = str(Path(self.model_dir) / "lexicon.txt")
            dict_dir = str(Path(self.model_dir) / "dict")

            if self.model_type == "vits":
                self._generator = sherpa.OfflineTts(
                    vits_model=model_path,
                    lexicon=lexicon_path if Path(lexicon_path).exists() else "",
                    tokens=tokens_path,
                    dict_dir=dict_dir if Path(dict_dir).exists() else "",
                    num_threads=2,
                    debug=False,
                )
            else:
                raise ValueError(f"Unsupported sherpa model type: {self.model_type}")
        return self._generator

    async def synthesize(self, text: str, voice: VoiceConfig, output_path: Path) -> Path:
        import asyncio

        generator = self._get_generator()

        # speaker_id from voice_id (VITS multi-speaker)
        speaker_id = int(voice.voice_id) if voice.voice_id and voice.voice_id.isdigit() else 0
        speed = voice.speed if voice.speed > 0 else 1.0

        # Run in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        audio = await loop.run_in_executor(
            None,
            lambda: generator.generate(text, sid=speaker_id, speed=speed),
        )

        # Write as WAV using sherpa-onnx's built-in writer
        import wave

        with wave.open(str(output_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(audio.sample_rate)
            wf.writeframes(audio.samples)
        return output_path

    def is_available(self) -> bool:
        return bool(self.model_dir) and Path(self.model_dir).exists()
