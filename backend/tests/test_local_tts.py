"""Tests for local TTS providers."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from tts.base import VoiceConfig
from tts.factory import create_tts_provider


def test_cosyvoice_local():
    p = create_tts_provider("cosyvoice_local", base_url="http://127.0.0.1:50000")
    assert p.engine_id == "cosyvoice_local"
    assert p.base_url == "http://127.0.0.1:50000"
    assert p.url() == "http://127.0.0.1:50000/api/tts"
    assert p.is_available() is True


def test_cosyvoice_local_payload():
    p = create_tts_provider("cosyvoice_local", base_url="http://localhost:50000")
    vc = VoiceConfig(engine="cosyvoice_local", voice_id="中文女")
    payload = p.build_payload("测试文本", vc)
    assert payload["text"] == "测试文本"
    assert payload["voice"] == "中文女"


def test_gpt_sovits():
    p = create_tts_provider("gpt_sovits", base_url="http://127.0.0.1:9880")
    assert p.engine_id == "gpt_sovits"
    assert p.url() == "http://127.0.0.1:9880/tts"


def test_gpt_sovits_payload_with_voice_id():
    p = create_tts_provider("gpt_sovits", base_url="http://localhost:9880")
    vc = VoiceConfig(
        engine="gpt_sovits",
        voice_id="/path/ref.wav:你好世界:zh",
    )
    payload = p.build_payload("文本", vc)
    assert payload["refer_wav_path"] == "/path/ref.wav"
    assert payload["prompt_text"] == "你好世界"
    assert payload["prompt_language"] == "zh"


def test_indextts():
    p = create_tts_provider("indextts", base_url="http://127.0.0.1:8000")
    assert p.engine_id == "indextts"
    assert p.url() == "http://127.0.0.1:8000/synthesize"


def test_fish_speech():
    p = create_tts_provider("fish_speech", base_url="http://127.0.0.1:8080")
    assert p.engine_id == "fish_speech"
    assert p.url() == "http://127.0.0.1:8080/v1/tts"


def test_f5_tts():
    p = create_tts_provider("f5_tts", base_url="http://127.0.0.1:7860")
    assert p.engine_id == "f5_tts"
    assert p.url() == "http://127.0.0.1:7860/synth"


def test_chattts():
    p = create_tts_provider("chattts", base_url="http://127.0.0.1:9999")
    assert p.engine_id == "chattts"
    assert p.url() == "http://127.0.0.1:9999/generate_audio"


def test_chattts_payload_with_seed():
    p = create_tts_provider("chattts", base_url="http://localhost:9999")
    vc = VoiceConfig(engine="chattts", voice_id="123")
    payload = p.build_payload("文本", vc)
    assert payload["speaker_seed"] == 123


def test_sherpa_vits():
    p = create_tts_provider("sherpa_vits", model_dir="/fake/path")
    assert p.engine_id == "sherpa_vits"
    assert p.is_available() is False  # /fake/path doesn't exist


def test_sherpa_kokoro():
    p = create_tts_provider("sherpa_kokoro", model_dir="/fake/path")
    assert p.engine_id == "sherpa_kokoro"
    assert p.is_available() is False


def test_http_local_parse_bytes():
    """Test parse_response with raw bytes."""
    from tts.http_local import HTTPLocalTTSProvider

    class Dummy(HTTPLocalTTSProvider):
        endpoint = "/test"
        engine_id = "dummy"

        def build_payload(self, text, voice):
            return {"text": text}

    d = Dummy(base_url="http://localhost:1234")
    assert d.parse_response(b"audio_data") == b"audio_data"


def test_http_local_parse_json():
    """Test parse_response with JSON containing base64 audio."""
    import base64

    from tts.http_local import HTTPLocalTTSProvider

    class Dummy(HTTPLocalTTSProvider):
        endpoint = "/test"
        engine_id = "dummy"

        def build_payload(self, text, voice):
            return {}

    d = Dummy(base_url="http://localhost:1234")
    encoded = base64.b64encode(b"audio_bytes").decode()
    result = d.parse_response({"audio": encoded})
    assert result == b"audio_bytes"


def test_all_12_engines_creatable():
    """Verify all 12 engines can be created via factory."""
    engines = [
        ("edge", {}),
        ("dashscope", {"api_key": "k"}),
        ("volcengine", {"app_id": "a", "access_token": "t"}),
        ("mimo", {"base_url": "http://x", "api_key": "k"}),
        ("cosyvoice_local", {"base_url": "http://x"}),
        ("gpt_sovits", {"base_url": "http://x"}),
        ("indextts", {"base_url": "http://x"}),
        ("fish_speech", {"base_url": "http://x"}),
        ("f5_tts", {"base_url": "http://x"}),
        ("chattts", {"base_url": "http://x"}),
        ("sherpa_vits", {"model_dir": "/x"}),
        ("sherpa_kokoro", {"model_dir": "/x"}),
    ]
    for engine_id, cfg in engines:
        p = create_tts_provider(engine_id, **cfg)
        assert p.engine_id == engine_id, f"Engine mismatch for {engine_id}"
