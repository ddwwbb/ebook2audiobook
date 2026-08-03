"""Audio merger — concat segments into chapters, chapters into final audiobook.

Uses ffmpeg via pydub/ffmpeg-cli concat.
"""

from __future__ import annotations

import asyncio
from pathlib import Path


async def concat_audio(files: list[Path], output: Path) -> Path:
    """Concatenate audio files into one using ffmpeg concat demuxer."""
    if not files:
        raise ValueError("No audio files to concat")

    list_file = output.with_suffix(".concat_list.txt")
    list_file.write_text(
        "\n".join(f"file '{f.resolve()}'" for f in files),
        encoding="utf-8",
    )

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(output),
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    list_file.unlink(missing_ok=True)

    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg concat failed: {stderr.decode()}")

    return output
