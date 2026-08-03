"""Audio synthesis and export endpoints with WebSocket progress.

The full end-to-end flow:
1. Client sends chapters SML + voice assignments via WS
2. Server synthesizes each segment via TTS provider
3. Concatenates into chapter audio
4. Exports final M4B with metadata + cover
5. Streams progress throughout
"""

from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, WebSocket
from pydantic import BaseModel

from audio.exporter import BookMetadata, Chapter, export_m4b
from audio.merger import concat_audio
from audio.synthesizer import CharacterVoice, synthesize_chapter
from api.sanitize import sanitize_error as _sanitize_error

router = APIRouter()


class CharacterVoiceConfig(BaseModel):
    name: str
    engine: str
    voice_id: str = ""
    reference_audio: str | None = None
    pitch: float = 0.0
    speed: float = 1.0


class GenerateRequest(BaseModel):
    """Full generation request sent via WebSocket first message."""

    title: str = "未命名"
    author: str = ""
    chapters: list[dict]  # [{index, title, sml}]

    # Voice assignments per character
    voices: list[CharacterVoiceConfig]

    # TTS engine configs (API keys etc.)
    engine_configs: dict[str, dict[str, Any]] = {}

    # Output config
    output_format: str = "m4b"  # m4b | mp3 | wav


@router.post("/start")
async def start_generation() -> dict:
    """Placeholder — actual generation runs via WebSocket."""
    return {"job_id": str(uuid.uuid4())[:8]}


@router.websocket("/run/{job_id}")
async def run_generation(websocket: WebSocket, job_id: str) -> None:
    """WebSocket: run full synthesis pipeline, stream progress, return download URL."""
    await websocket.accept()

    try:
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=30)
        req = GenerateRequest(**json.loads(raw))
    except (asyncio.TimeoutError, json.JSONDecodeError, ValueError) as exc:
        await websocket.send_json({"type": "error", "message": f"Invalid request: {exc}"})
        await websocket.close()
        return

    work_dir = Path(f"/tmp/audiobook_{job_id}")
    work_dir.mkdir(parents=True, exist_ok=True)

    # Build character voice map
    char_voices = {
        v.name: CharacterVoice(
            name=v.name,
            engine=v.engine,
            voice_id=v.voice_id,
            reference_audio=v.reference_audio,
            pitch=v.pitch,
            speed=v.speed,
        )
        for v in req.voices
    }
    # Ensure 旁白 has a voice
    if "旁白" not in char_voices:
        char_voices["旁白"] = CharacterVoice(name="旁白", engine="edge")

    total_chapters = len(req.chapters)
    chapter_audios: list[Path] = []
    chapter_offsets: list[tuple[str, int, int]] = []  # (title, start_ms, end_ms)
    current_offset_ms = 0

    await websocket.send_json({
        "type": "generation_start",
        "total_chapters": total_chapters,
    })

    for ch in req.chapters:
        ch_idx = ch["index"]
        ch_title = ch["title"]
        ch_sml = ch["sml"]

        # Fix #6: use default args to capture loop variables by value, not by reference
        async def on_progress(prog, _idx=ch_idx, _title=ch_title) -> None:
            await websocket.send_json({
                "type": "chapter_progress",
                "chapter": _idx,
                "chapter_title": _title,
                "current_segment": prog.current_segment,
                "total_segments": prog.total_segments,
                "text_preview": prog.text_preview,
            })

        try:
            result = await synthesize_chapter(
                sml_text=ch_sml,
                chapter_index=ch_idx,
                character_voices=char_voices,
                work_dir=work_dir,
                engine_configs=req.engine_configs,
                on_progress=on_progress,
            )
            chapter_audios.append(result.audio_path)
            chapter_offsets.append((ch_title, current_offset_ms, current_offset_ms + result.duration_ms))
            current_offset_ms += result.duration_ms

            await websocket.send_json({
                "type": "chapter_done",
                "chapter": ch_idx,
                "chapter_title": ch_title,
                "duration_ms": result.duration_ms,
                "warnings": result.errors if result.errors else [],
            })

        except Exception as exc:
            # Fix #3: sanitize error to avoid leaking API keys
            safe_msg = _sanitize_error(str(exc))
            await websocket.send_json({
                "type": "chapter_error",
                "chapter": ch_idx,
                "error": safe_msg,
            })

    if not chapter_audios:
        await websocket.send_json({"type": "error", "message": "No audio generated"})
        await websocket.close()
        return

    # Concat all chapters into final audio
    await websocket.send_json({"type": "merging", "chapters": len(chapter_audios)})
    final_audio = work_dir / "final_audio.wav"
    await concat_audio(chapter_audios, final_audio)

    # Export with metadata + chapters
    metadata = BookMetadata(title=req.title, author=req.author, language="zh")
    chapters_meta = [
        Chapter(title=title, start_ms=start, end_ms=end)
        for title, start, end in chapter_offsets
    ]

    output_ext = req.output_format if req.output_format in ("m4b", "mp3", "wav") else "m4b"
    output_path = work_dir / f"{req.title}.{output_ext}"

    await export_m4b(
        audio_path=final_audio,
        metadata=metadata,
        chapters=chapters_meta,
        cover_path=None,
        output_path=output_path,
    )

    await websocket.send_json({
        "type": "generation_done",
        "output_path": str(output_path),
        "total_duration_ms": current_offset_ms,
        "chapters": len(chapter_audios),
    })

    await websocket.close()
