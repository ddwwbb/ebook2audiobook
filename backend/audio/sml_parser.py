"""SML (Speech Markup Language) parser.

Splits text containing [voice:...]...[/voice], [pause:N], [break] tags into segments.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

SML_PATTERN = re.compile(
    r"\[voice:(?P<voice>[^\]]+)\]|"
    r"\[/voice\]|"
    r"\[pause:(?P<pause_sec>[\d.]+)\]|"
    r"\[pause\]|"
    r"\[break\]",
)


@dataclass
class Segment:
    kind: Literal["text", "pause"]
    text: str = ""
    voice: str | None = None  # speaker name or wav path
    pause_seconds: float = 0.0


def parse_sml(sml_text: str, default_voice: str = "旁白") -> list[Segment]:
    """Parse SML-tagged text into ordered segments.

    Handles both macro mode [voice:角色名] and path mode [voice:/abs/path.wav].
    """
    segments: list[Segment] = []
    current_voice: str | None = None
    last_pos = 0

    for match in SML_PATTERN.finditer(sml_text):
        # Emit any text before this tag
        text_before = sml_text[last_pos:match.start()].strip()
        if text_before:
            segments.append(
                Segment(
                    kind="text",
                    text=text_before,
                    voice=current_voice or default_voice,
                )
            )

        tag = match.group(0)

        if tag.startswith("[voice:"):
            current_voice = match.group("voice")
        elif tag == "[/voice]":
            current_voice = None
        elif tag.startswith("[pause:"):
            segments.append(Segment(kind="pause", pause_seconds=float(match.group("pause_sec"))))
        elif tag == "[pause]":
            segments.append(Segment(kind="pause", pause_seconds=1.0))
        elif tag == "[break]":
            segments.append(Segment(kind="pause", pause_seconds=0.4))

        last_pos = match.end()

    # Trailing text
    trailing = sml_text[last_pos:].strip()
    if trailing:
        segments.append(
            Segment(
                kind="text",
                text=trailing,
                voice=current_voice or default_voice,
            )
        )

    return segments
