"""Single-pass role recognition pipeline.

One LLM call per chapter. Accumulates a global role table across chapters
for cross-chapter consistency.
"""

from __future__ import annotations

import logging

import tenacity

from llm.client import LLMClient, LLMConfig, LLMMessage
from llm.factory import extract_json
from llm.prompts import load_prompt, render_prompt
from pipeline.progress import ProgressCallback, make_event, noop_progress
from pipeline.types import Chapter, ChapterResult, Role

logger = logging.getLogger(__name__)

# Max characters per LLM call chunk — prevents exceeding context window
MAX_CHUNK_CHARS = 8000


def _format_known_roles(roles: list[Role]) -> str:
    if not roles:
        return "（暂无已知角色）"
    lines = []
    for r in roles:
        info = f"- {r.name}（{r.gender}, {r.age}）"
        if r.aliases:
            info += f"  别名：{'、'.join(r.aliases)}"
        lines.append(info)
    return "\n".join(lines)


def _split_long_text(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split text by paragraphs to stay under max_chars."""
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for para in text.split("\n"):
        if current_len + len(para) > max_chars and current:
            chunks.append("\n".join(current))
            current = [para]
            current_len = len(para)
        else:
            current.append(para)
            current_len += len(para) + 1
    if current:
        chunks.append("\n".join(current))
    return chunks


def _merge_roles(existing: list[Role], new_roles: list[dict]) -> list[Role]:
    """Merge newly detected roles into the existing table, dedup by name."""
    by_name = {r.name: r for r in existing}
    for r in new_roles:
        name = r.get("name", "").strip()
        if not name:
            continue
        if name in by_name:
            # Update missing fields
            existing_role = by_name[name]
            if existing_role.gender == "unknown" and r.get("gender"):
                existing_role.gender = r["gender"]
            if existing_role.age == "unknown" and r.get("age"):
                existing_role.age = r["age"]
            for alias in r.get("aliases", []):
                if alias and alias not in existing_role.aliases:
                    existing_role.aliases.append(alias)
        else:
            by_name[name] = Role(
                name=name,
                gender=r.get("gender", "unknown"),
                age=r.get("age", "unknown"),
                aliases=r.get("aliases", []),
                role=r.get("role", ""),
            )
    return list(by_name.values())


@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=30),
    retry=tenacity.retry_if_exception_type(Exception),
    before_sleep=tenacity.before_sleep_log(logger, logging.WARNING),
)
async def _call_llm(client: LLMClient, config: LLMConfig, messages: list[LLMMessage]) -> str:
    """Call LLM with retry. Returns raw text output."""
    return await client.complete_json(messages, config)


async def process_chapter(
    chapter: Chapter,
    client: LLMClient,
    config: LLMConfig,
    known_roles: list[Role],
    on_progress: ProgressCallback = noop_progress,
) -> ChapterResult:
    """Process a single chapter: text → SML + roles."""
    await on_progress(
        make_event("chapter_start", chapter.index, sml_preview="", roles=[])
    )

    template = load_prompt("single_pass")
    roles_str = _format_known_roles(known_roles)

    # Split long chapters
    chunks = _split_long_text(chapter.text)
    sml_parts: list[str] = []
    all_roles: list[dict] = []

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
            logger.error("Chapter %d chunk %d failed: %s", chapter.index, i, exc)
            # Fallback: treat the chunk as pure narration
            sml_parts.append(f"[voice:旁白]{chunk}[/voice]")
            await on_progress(
                make_event(
                    "chunk_error",
                    chapter.index,
                    chunk=i,
                    error=str(exc),
                )
            )
            continue

        parsed = extract_json(raw)
        if parsed and isinstance(parsed, dict):
            sml_parts.append(parsed.get("sml", f"[voice:旁白]{chunk}[/voice]"))
            chunk_roles = parsed.get("roles", [])
            if isinstance(chunk_roles, list):
                all_roles.extend(chunk_roles)
        else:
            logger.warning("Chapter %d chunk %d: unparseable LLM output", chapter.index, i)
            sml_parts.append(f"[voice:旁白]{chunk}[/voice]")

        # Stream a preview of the SML so far
        await on_progress(
            make_event(
                "chunk_done",
                chapter.index,
                sml_preview=sml_parts[-1][:500],
                roles_found=[r.get("name", "") for r in all_roles],
            )
        )

    sml = "\n[pause:0.4]\n".join(sml_parts)
    await on_progress(
        make_event("chapter_done", chapter.index, sml_preview=sml[:500])
    )

    return ChapterResult(
        chapter_index=chapter.index,
        sml=sml,
        roles_appeared=[r.get("name", "") for r in all_roles if r.get("name")],
        roles_data=all_roles,
    )


async def run(
    chapters: list[Chapter],
    client: LLMClient,
    config: LLMConfig,
    on_progress: ProgressCallback = noop_progress,
) -> tuple[list[ChapterResult], list[Role]]:
    """Run single-pass recognition across all chapters.

    Returns (chapter_results, global_role_table).
    """
    results: list[ChapterResult] = []
    global_roles: list[Role] = []
    total = len(chapters)

    await on_progress(make_event("pipeline_start", total_chapters=total, mode="single_pass"))

    for chapter in chapters:
        result = await process_chapter(
            chapter, client, config, global_roles, on_progress
        )
        # Accumulate newly detected roles into the global table
        global_roles = _merge_roles(global_roles, result.roles_data)
        results.append(result)
        await on_progress(
            make_event(
                "pipeline_progress",
                chapter.index + 1,
                total,
                roles_count=len(global_roles),
            )
        )

    await on_progress(make_event("pipeline_done", total_chapters=total))
    return results, global_roles
