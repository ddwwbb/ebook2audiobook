"""Progress reporter for pipeline — pushes events to WebSocket clients."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

# Progress callback: async function that receives an event dict
ProgressCallback = Callable[[dict[str, Any]], Awaitable[None]]


async def noop_progress(event: dict[str, Any]) -> None:
    """Default no-op progress callback."""
    pass


def make_event(
    event_type: str,
    chapter_index: int | None = None,
    total_chapters: int | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Build a progress event dict."""
    event: dict[str, Any] = {"type": event_type}
    if chapter_index is not None:
        event["chapter"] = chapter_index
    if total_chapters is not None:
        event["total"] = total_chapters
    event.update(extra)
    return event
