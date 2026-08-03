"""M4B/MP3 exporter with metadata and cover art."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BookMetadata:
    title: str = ""
    author: str = ""
    language: str = "zh"
    year: str = ""


@dataclass
class Chapter:
    title: str
    start_ms: int  # milliseconds from book start
    end_ms: int


async def export_m4b(
    audio_path: Path,
    metadata: BookMetadata,
    chapters: list[Chapter],
    cover_path: Path | None,
    output_path: Path,
) -> Path:
    """Export final M4B with FFMETADATA, chapters, and cover art."""
    meta_file = output_path.with_suffix(".ffmeta")
    lines = [";FFMETADATA1"]
    if metadata.title:
        lines.append(f"title={metadata.title}")
    if metadata.author:
        lines.append(f"artist={metadata.author}")
    if metadata.language:
        lines.append(f"language={metadata.language}")
    if metadata.year:
        lines.append(f"year={metadata.year}")

    for ch in chapters:
        lines.append("[CHAPTER]")
        lines.append("TIMEBASE=1/1000")
        lines.append(f"START={ch.start_ms}")
        lines.append(f"END={ch.end_ms}")
        lines.append(f"title={ch.title}")

    meta_file.write_text("\n".join(lines), encoding="utf-8")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(audio_path),
    ]
    if cover_path and cover_path.exists():
        cmd += ["-i", str(cover_path), "-map", "0:a", "-map", "1:v"]
    else:
        cmd += ["-map", "0:a"]

    cmd += [
        "-i", str(meta_file),
        "-map_metadata", "2",
        "-c:a", "aac", "-b:a", "96k",
    ]
    # Fix #5: properly handle video codec based on cover presence
    has_cover = cover_path is not None and cover_path.exists()
    if has_cover:
        cmd += ["-c:v", "mjpeg"]
    else:
        cmd += ["-vn"]
    cmd += [str(output_path)]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    meta_file.unlink(missing_ok=True)

    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg export failed: {stderr.decode()}")

    return output_path
