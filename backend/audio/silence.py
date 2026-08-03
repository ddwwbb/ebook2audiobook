"""Generate silence audio files for [pause] and [break] SML tags."""

from __future__ import annotations

import asyncio
from pathlib import Path


async def generate_silence(duration_sec: float, output_path: Path, sample_rate: int = 24000) -> Path:
    """Generate a silent audio segment using ffmpeg."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"anullsrc=r={sample_rate}:cl=mono",
        "-t", str(duration_sec),
        "-c:a", "pcm_s16le",
        str(output_path),
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg silence generation failed: {stderr.decode()}")
    return output_path
