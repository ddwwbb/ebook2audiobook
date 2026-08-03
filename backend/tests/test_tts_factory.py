"""Tests for TTS provider factory."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from tts.factory import create_tts_provider


def test_create_edge():
    p = create_tts_provider("edge")
    assert p.engine_id == "edge"
    assert p.is_available() is True


def test_create_dashscope():
    p = create_tts_provider("dashscope", api_key="sk-test")
    assert p.engine_id == "dashscope"
    assert p.is_available() is True

    p2 = create_tts_provider("dashscope")
    assert p2.is_available() is False  # no api key


def test_create_volcengine():
    p = create_tts_provider("volcengine", app_id="123", access_token="tok")
    assert p.engine_id == "volcengine"
    assert p.is_available() is True


def test_create_mimo():
    p = create_tts_provider("mimo", base_url="https://api.mimo.com", api_key="k")
    assert p.engine_id == "mimo"
    assert p.is_available() is True
    assert p.base_url == "https://api.mimo.com"


def test_create_unknown():
    with pytest.raises(ValueError, match="Unknown TTS engine"):
        create_tts_provider("nonexistent")


def test_edge_voices_map():
    from tts.edge import ZH_VOICES
    assert "female_xiaoyi" in ZH_VOICES
    assert ZH_VOICES["female_xiaoyi"] == "zh-CN-XiaoyiNeural"
    assert "male_yunxi" in ZH_VOICES


def test_mimo_reference_loading():
    from tts.base import VoiceConfig
    from tts.mimo import MimoTTSProvider
    # Create a fake reference audio file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(b"fake_audio_data")
        ref_path = f.name

    try:
        p = MimoTTSProvider(api_key="k")
        b64 = p._load_reference_base64(ref_path)
        assert isinstance(b64, str)
        # Verify it decodes back
        import base64
        assert base64.b64decode(b64) == b"fake_audio_data"
    finally:
        Path(ref_path).unlink()
