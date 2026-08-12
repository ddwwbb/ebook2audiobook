import os
import importlib.util
import tempfile
import unittest
import wave
from io import BytesIO
from unittest.mock import Mock, patch

MODULE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "lib",
    "classes",
    "tts_engines",
    "ai_voice.py",
)
MODULE_SPEC = importlib.util.spec_from_file_location("ai_voice_adapter", MODULE_PATH)
AI_VOICE_MODULE = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(AI_VOICE_MODULE)
AiVoice = AI_VOICE_MODULE.AiVoice


def make_wav() -> bytes:
    output = BytesIO()
    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x00\x00" * 160)
    return output.getvalue()


class AiVoiceTest(unittest.TestCase):

    @patch.dict(os.environ, {"AI_VOICE_API_KEY": "test-key", "AI_VOICE_TTS_PROVIDER": "edge"}, clear=False)
    def test_convert_writes_audio_and_sends_auth(self):
        engine = AiVoice({})
        response = Mock(status_code=200, content=make_wav(), headers={"Content-Type": "audio/wav"})
        response.iter_content = Mock(return_value=iter([response.content]))
        engine.http.post = Mock(return_value=response)

        with tempfile.TemporaryDirectory() as temp_dir:
            output = os.path.join(temp_dir, "sentence.wav")
            success, error = engine.convert(output, "hello")

            self.assertTrue(success)
            self.assertIsNone(error)
            self.assertGreater(os.path.getsize(output), 0)

        request = engine.http.post.call_args
        self.assertEqual("Bearer test-key", request.kwargs["headers"]["Authorization"])
        self.assertEqual("edge", request.kwargs["json"]["provider"])
        self.assertNotIn("format", request.kwargs["json"])
        self.assertTrue(request.kwargs["stream"])

    @patch.dict(os.environ, {"AI_VOICE_API_KEY": ""}, clear=False)
    def test_api_key_is_required(self):
        with self.assertRaisesRegex(ValueError, "AI_VOICE_API_KEY"):
            AiVoice({})

    @patch.dict(os.environ, {"AI_VOICE_API_KEY": "test-key"}, clear=False)
    def test_mislabeled_audio_is_rejected(self):
        engine = AiVoice({})
        response = Mock(
            status_code=200,
            content=b"ID3\x04\x00\x00",
            headers={"Content-Type": "audio/wav"},
        )
        response.iter_content = Mock(return_value=iter([response.content]))
        engine.http.post = Mock(return_value=response)

        with tempfile.TemporaryDirectory() as temp_dir:
            output = os.path.join(temp_dir, "sentence.wav")
            success, error = engine.convert(output, "hello")

        self.assertFalse(success)
        self.assertIn("ValueError", error)


if __name__ == "__main__":
    unittest.main()
