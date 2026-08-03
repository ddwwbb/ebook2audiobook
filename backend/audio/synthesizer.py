"""Synthesis orchestrator: SML text → per-segment TTS → concat → chapter audio.

This is the core engine that ties SML parsing, TTS providers, and audio
merging together for end-to-end audiobook generation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from audio.merger import concat_audio
from audio.silence import generate_silence
from audio.sml_parser import parse_sml
from tts.base import VoiceConfig
from tts.factory import create_tts_provider

logger = logging.getLogger(__name__)


@dataclass
class CharacterVoice:
    """Maps a character name to a TTS engine + voice config."""
    name: str
    engine: str
    voice_id: str = ""
    reference_audio: str | None = None
    pitch: float = 0.0
    speed: float = 1.0


@dataclass
class SynthesisProgress:
    chapter_index: int
    total_segments: int
    current_segment: int
    text_preview: str = ""


@dataclass
class ChapterAudioResult:
    chapter_index: int
    audio_path: Path
    duration_ms: int
    segments_count: int
    errors: list[str] = field(default_factory=list)


async def synthesize_chapter(
    sml_text: str,
    chapter_index: int,
    character_voices: dict[str, CharacterVoice],
    work_dir: Path,
    engine_configs: dict[str, dict[str, Any]] | None = None,
    on_progress=None,
) -> ChapterAudioResult:
    """Synthesize one chapter's SML text into a single audio file.

    Args:
        sml_text: SML-tagged text from the role recognition pipeline.
        chapter_index: Chapter number for naming.
        character_voices: {character_name: CharacterVoice} mapping.
        work_dir: Temp directory for intermediate audio segments.
        engine_configs: {engine_id: {api_key, ...}} for provider creation.
        on_progress: async callback(SynthesisProgress).

    Returns:
        ChapterAudioResult with the final concatenated audio path.
    """
    engine_configs = engine_configs or {}
    chapter_dir = work_dir / f"chapter_{chapter_index}"
    chapter_dir.mkdir(parents=True, exist_ok=True)

    synthesis_errors: list[str] = []

    segments = parse_sml(sml_text)
    segment_files: list[Path] = []

    # Cache providers to avoid recreating for each segment
    providers: dict[str, Any] = {}

    for i, seg in enumerate(segments):
        if on_progress:
            await on_progress(
                SynthesisProgress(
                    chapter_index=chapter_index,
                    total_segments=len(segments),
                    current_segment=i,
                    text_preview=seg.text[:80] if seg.text else f"[pause {seg.pause_seconds}s]",
                )
            )

        seg_path = chapter_dir / f"{i:04d}.wav"

        if seg.kind == "pause":
            await generate_silence(seg.pause_seconds, seg_path)
            segment_files.append(seg_path)
            continue

        # Text segment — find the voice for this character
        char_voice = character_voices.get(seg.voice or "旁白")
        if not char_voice:
            # Fallback to edge TTS default
            char_voice = CharacterVoice(name=seg.voice or "旁白", engine="edge")

        # Get or create provider
        if char_voice.engine not in providers:
            cfg = engine_configs.get(char_voice.engine, {})
            providers[char_voice.engine] = create_tts_provider(char_voice.engine, **cfg)

        provider = providers[char_voice.engine]
        voice_config = VoiceConfig(
            engine=char_voice.engine,
            voice_id=char_voice.voice_id,
            reference_audio=char_voice.reference_audio,
            pitch=char_voice.pitch,
            speed=char_voice.speed,
        )

        try:
            await provider.synthesize(seg.text, voice_config, seg_path)
            segment_files.append(seg_path)
        except Exception as exc:
            # Fix #8: log AND collect errors so the caller/user is informed
            error_msg = f"第{chapter_index + 1}章 段落{i} 合成失败（{char_voice.engine}）: {exc}，已用静音替代"
            logger.warning(error_msg)
            synthesis_errors.append(error_msg)
            await generate_silence(1.0, seg_path)
            segment_files.append(seg_path)

    # Concat all segments into chapter audio
    chapter_audio = chapter_dir / "chapter_full.wav"
    if segment_files:
        await concat_audio(segment_files, chapter_audio)
    else:
        await generate_silence(1.0, chapter_audio)

    # Get duration
    duration_ms = await _get_duration_ms(chapter_audio)

    return ChapterAudioResult(
        chapter_index=chapter_index,
        audio_path=chapter_audio,
        duration_ms=duration_ms,
        segments_count=len(segment_files),
        errors=synthesis_errors,
    )


async def _get_duration_ms(audio_path: Path) -> int:
    """Get audio duration in milliseconds using ffprobe."""
    import asyncio

    proc = await asyncio.create_subprocess_exec(
        "ffprobe",
        "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "csv=p=0",
        str(audio_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    try:
        duration_sec = float(stdout.decode().strip())
        return int(duration_sec * 1000)
    except (ValueError, IndexError):
        return 0
