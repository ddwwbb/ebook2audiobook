"""sherpa-onnx Kokoro provider — lightweight 82M model for ARM/embedded.

Kokoro uses the Matcha-TTS frontend in sherpa-onnx.
Best choice for RK3588 / ARM Linux (official RKNN NPU acceleration).

No zero-shot cloning — fixed voice set.
"""

from __future__ import annotations

from pathlib import Path

from tts.base import TTSProvider, VoiceConfig
from tts.sherpa_vits import SherpaVITSProvider, _import_sherpa


class SherpaKokoroProvider(SherpaVITSProvider):
    engine_id = "sherpa_kokoro"

    """sherpa-onnx Kokoro — 82M, ARM/RK3588 friendly."""

    def __init__(self, model_dir: str = "", model_type: str = "kokoro"):
        super().__init__(model_dir=model_dir, model_type=model_type)

    def _get_generator(self):
        if self._generator is None:
            sherpa = _import_sherpa()
            model_path = str(Path(self.model_dir) / "model.onnx")
            tokens_path = str(Path(self.model_dir) / "tokens.txt")
            voices_path = str(Path(self.model_dir) / "voices.bin")
            data_dir = str(Path(self.model_dir) / "espeak-ng-data")

            self._generator = sherpa.OfflineTts(
                kokoro_model=model_path,
                voices=voices_path,
                tokens=tokens_path,
                data_dir=data_dir,
                num_threads=2,
                debug=False,
            )
        return self._generator
