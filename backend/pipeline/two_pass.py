"""Two-pass role recognition pipeline.

Pass 1: Sample a subset of chapters to extract a global character table.
Pass 2: Use that character table to assign speakers in every chapter.

More accurate than single-pass for cross-chapter consistency, but costs
~2x LLM calls (sampling + full assignment).
"""

from __future__ import annotations

import logging
import random

import tenacity

from llm.client import LLMClient, LLMConfig, LLMMessage
from llm.factory import extract_json
from llm.prompts import load_prompt, render_prompt
from pipeline.progress import ProgressCallback, make_event, noop_progress
from pipeline.single_pass import (
    _call_llm,
    _format_known_roles,
    _merge_roles,
    _split_long_text,
)
from pipeline.types import Chapter, ChapterResult, Role

logger = logging.getLogger(__name__)

# How many chapters to sample for pass 1
DEFAULT_SAMPLE_COUNT = 5
MAX_SAMPLE_CHARS = 4000  # Max chars per sampled chapter in pass 1


def _select_sample_chapters(chapters: list[Chapter], sample_count: int) -> list[Chapter]:
    """Select chapters for sampling: first + last + random middle."""
    if len(chapters) <= sample_count:
        return chapters

    sample = [chapters[0], chapters[-1]]
    middle = chapters[1:-1]
    remaining = sample_count - 2
    if remaining > 0 and middle:
        sample.extend(random.sample(middle, min(remaining, len(middle))))
    return sample


async def extract_roles(
    chapters: list[Chapter],
    client: LLMClient,
    config: LLMConfig,
    sample_count: int = DEFAULT_SAMPLE_COUNT,
    on_progress: ProgressCallback = noop_progress,
) -> list[Role]:
    """Pass 1: Sample chapters to extract a global character table."""
    template = load_prompt("two_pass_extract")
    sampled = _select_sample_chapters(chapters, sample_count)

    await on_progress(
        make_event("pass1_start", total_chapters=len(chapters), sampled=len(sampled))
    )

    global_roles: list[Role] = []

    for ch in sampled:
        # Truncate long chapters for sampling
        text = ch.text[:MAX_SAMPLE_CHARS]
        prompt = render_prompt(template, chapter_text=text)
        messages = [LLMMessage(role="user", content=prompt)]

        try:
            raw = await _call_llm(client, config, messages)
            parsed = extract_json(raw)
            if parsed and isinstance(parsed, dict):
                roles_data = parsed.get("roles", [])
                if isinstance(roles_data, list):
                    global_roles = _merge_roles(global_roles, roles_data)
        except Exception as exc:
            logger.warning("Pass 1 sampling chapter %d failed: %s", ch.index, exc)

        await on_progress(
            make_event("pass1_progress", ch.index, roles_found=len(global_roles))
        )

    await on_progress(make_event("pass1_done", roles_found=len(global_roles)))
    return global_roles


async def assign_chapter(
    chapter: Chapter,
    client: LLMClient,
    config: LLMConfig,
    known_roles: list[Role],
    on_progress: ProgressCallback = noop_progress,
) -> ChapterResult:
    """Pass 2: Assign speakers in a single chapter using the known role table."""
    template = load_prompt("two_pass_assign")
    roles_str = _format_known_roles(known_roles)
    chunks = _split_long_text(chapter.text)

    sml_parts: list[str] = []
    roles_appeared: list[str] = []

    for i, chunk in enumerate(chunks):
        prompt = render_prompt(
            template,
            known_roles=roles_str,
            chapter_title=chapter.title if i == 0 else f"{chapter.title}（续 {i+1}）",
            chapter_text=chunk,
        )
        messages = [LLMMessage(role="user", content=prompt)]

        try:
            raw = await _call_llm(client, config, messages)
        except Exception as exc:
            logger.error("Pass 2 chapter %d chunk %d failed: %s", chapter.index, i, exc)
            sml_parts.append(f"[voice:旁白]{chunk}[/voice]")
            await on_progress(
                make_event("chunk_error", chapter.index, chunk=i, error=str(exc))
            )
            continue

        parsed = extract_json(raw)
        if parsed and isinstance(parsed, dict):
            sml_parts.append(parsed.get("sml", f"[voice:旁白]{chunk}[/voice]"))
            appeared = parsed.get("roles_appeared", [])
            if isinstance(appeared, list):
                roles_appeared.extend(appeared)
        else:
            sml_parts.append(f"[voice:旁白]{chunk}[/voice]")

        await on_progress(
            make_event(
                "chunk_done",
                chapter.index,
                sml_preview=sml_parts[-1][:500],
            )
        )

    sml = "\n[pause:0.4]\n".join(sml_parts)
    await on_progress(make_event("chapter_done", chapter.index, sml_preview=sml[:500]))

    return ChapterResult(
        chapter_index=chapter.index,
        sml=sml,
        roles_appeared=list(set(roles_appeared)),
    )


async def run(
    chapters: list[Chapter],
    client: LLMClient,
    config: LLMConfig,
    on_progress: ProgressCallback = noop_progress,
    sample_count: int = DEFAULT_SAMPLE_COUNT,
) -> tuple[list[ChapterResult], list[Role]]:
    """Run two-pass recognition across all chapters.

    Returns (chapter_results, global_role_table).
    """
    total = len(chapters)

    # Pass 1: Extract roles from sampled chapters
    global_roles = await extract_roles(
        chapters, client, config, sample_count, on_progress
    )

    # Pass 2: Assign speakers in every chapter
    await on_progress(make_event("pass2_start", total_chapters=total))
    results: list[ChapterResult] = []

    for chapter in chapters:
        result = await assign_chapter(
            chapter, client, config, global_roles, on_progress
        )
        results.append(result)
        await on_progress(
            make_event("pipeline_progress", chapter.index + 1, total)
        )

    await on_progress(make_event("pipeline_done", total_chapters=total))
    return results, global_roles
