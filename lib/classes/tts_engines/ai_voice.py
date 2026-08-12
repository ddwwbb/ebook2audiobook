import io
import os
from pathlib import Path
from urllib.parse import urlparse

import requests

from lib.classes.tts_registry import TTSRegistry


class AiVoice(TTSRegistry, name="ai_voice"):
    """通过独立部署的 ai-voice 服务生成句子音频。"""

    def __init__(self, session):
        super().__init__(session)
        self.base_url = os.environ.get("AI_VOICE_BASE_URL", "http://127.0.0.1:8093").rstrip("/")
        self.api_key = os.environ.get("AI_VOICE_API_KEY", "").strip()
        self.provider = os.environ.get("AI_VOICE_TTS_PROVIDER", "edge").strip()
        self.voice = os.environ.get("AI_VOICE_TTS_VOICE", "").strip() or None
        self.timeout_seconds = self._read_timeout()
        self.max_audio_bytes = self._read_max_audio_bytes()
        self.http = requests.Session()
        self.tts_key = "ai_voice"
        self._validate_configuration()

    def _read_timeout(self) -> float:
        raw_timeout = os.environ.get("AI_VOICE_TIMEOUT_SECONDS", "120")
        try:
            timeout = float(raw_timeout)
        except ValueError as exc:
            raise ValueError("AI_VOICE_TIMEOUT_SECONDS must be a number") from exc
        if timeout <= 0 or timeout > 600:
            raise ValueError("AI_VOICE_TIMEOUT_SECONDS must be between 0 and 600")
        return timeout

    def _validate_configuration(self) -> None:
        parsed = urlparse(self.base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("AI_VOICE_BASE_URL must be an absolute HTTP(S) URL")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("AI_VOICE_BASE_URL must not contain credentials")
        if not self.api_key:
            raise ValueError("AI_VOICE_API_KEY is required")
        if not self.provider:
            raise ValueError("AI_VOICE_TTS_PROVIDER is required")

    @staticmethod
    def _read_max_audio_bytes() -> int:
        raw_limit = os.environ.get("AI_VOICE_MAX_AUDIO_BYTES", str(20 * 1024 * 1024))
        try:
            limit = int(raw_limit)
        except ValueError as exc:
            raise ValueError("AI_VOICE_MAX_AUDIO_BYTES must be an integer") from exc
        if limit <= 0 or limit > 100 * 1024 * 1024:
            raise ValueError("AI_VOICE_MAX_AUDIO_BYTES must be between 1 and 104857600")
        return limit

    def _set_voice(self, block_voice: str | None) -> tuple:
        if block_voice and os.path.isfile(block_voice):
            return None, "ai-voice does not accept local voice files; configure AI_VOICE_TTS_VOICE"
        return block_voice or self.voice, None

    def convert(self, sentence_file: str, sentence: str, **kwargs) -> tuple:
        if not sentence or not sentence.strip():
            return False, "Sentence is empty"

        voice, error = self._set_voice(kwargs.get("block_voice"))
        if error is not None:
            return False, error

        payload = {"text": sentence, "provider": self.provider}
        if voice:
            payload["voice"] = voice

        try:
            response = self.http.post(
                f"{self.base_url}/api/tts",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=(10, self.timeout_seconds),
                stream=True,
            )
            try:
                if response.status_code != 200:
                    return False, f"ai-voice TTS failed with HTTP {response.status_code}"
                audio_content = self._read_audio(response)
                if not audio_content:
                    return False, "ai-voice TTS returned an empty response"

                source_format = self._response_format(response.headers, audio_content)
                target_format = Path(sentence_file).suffix.lstrip(".").lower()
                if not target_format:
                    return False, "Sentence output file has no audio extension"

                Path(sentence_file).parent.mkdir(parents=True, exist_ok=True)
                if source_format == target_format:
                    Path(sentence_file).write_bytes(audio_content)
                else:
                    from pydub import AudioSegment

                    audio = AudioSegment.from_file(io.BytesIO(audio_content), format=source_format)
                    audio.export(sentence_file, format=target_format)
            finally:
                response.close()
            if not os.path.isfile(sentence_file) or os.path.getsize(sentence_file) == 0:
                return False, f"Cannot create {sentence_file}"
            return True, None
        except requests.RequestException as exc:
            return False, f"ai-voice request failed: {exc.__class__.__name__}"
        except Exception as exc:
            return False, f"ai-voice audio conversion failed: {exc.__class__.__name__}"

    def _read_audio(self, response: requests.Response) -> bytes:
        content_length = response.headers.get("Content-Length")
        if content_length:
            try:
                parsed_length = int(content_length)
            except ValueError as exc:
                raise ValueError("ai-voice returned an invalid Content-Length") from exc
            if parsed_length < 0:
                raise ValueError("ai-voice returned an invalid Content-Length")
            if parsed_length > self.max_audio_bytes:
                raise ValueError("ai-voice response exceeds audio size limit")

        content = bytearray()
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            content.extend(chunk)
            if len(content) > self.max_audio_bytes:
                raise ValueError("ai-voice response exceeds audio size limit")
        return bytes(content)

    @staticmethod
    def _response_format(headers: dict, content: bytes) -> str:
        content_type = headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        header_format = None
        if content_type in {"audio/mpeg", "audio/mp3"}:
            header_format = "mp3"
        elif content_type in {"audio/wav", "audio/wave", "audio/x-wav"}:
            header_format = "wav"

        payload_format = None
        if content.startswith(b"RIFF") and content[8:12] == b"WAVE":
            payload_format = "wav"
        elif content.startswith(b"ID3") or (
                len(content) > 1 and content[0] == 0xFF and content[1] & 0xE0 == 0xE0
        ):
            payload_format = "mp3"
        if payload_format is None:
            raise ValueError("ai-voice returned an unsupported audio format")
        if header_format is not None and header_format != payload_format:
            raise ValueError("ai-voice Content-Type does not match its audio payload")
        return payload_format
