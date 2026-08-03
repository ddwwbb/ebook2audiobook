"""Shared types for the role recognition pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Role:
    name: str
    gender: str = "unknown"  # male/female/unknown
    age: str = "unknown"     # child/teen/adult/elder/unknown
    aliases: list[str] = field(default_factory=list)
    role: str = ""           # 主角/配角/旁白


@dataclass
class Chapter:
    index: int
    title: str
    text: str


@dataclass
class ChapterResult:
    """Result of processing one chapter."""
    chapter_index: int
    sml: str
    roles_appeared: list[str] = field(default_factory=list)
    roles_data: list[dict] = field(default_factory=list)
    error: str | None = None
