"""Role recognition endpoints (single-pass / two-pass).

POST /api/roles/recognize  — start recognition job, returns job_id
WS   /api/roles/stream/{job_id}  — stream progress + results
"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

from fastapi import APIRouter, WebSocket
from pydantic import BaseModel

from llm.client import LLMConfig
from llm.factory import create_client
from pipeline.progress import make_event
from api.sanitize import sanitize_error as _sanitize_error

router = APIRouter()

# In-memory job store (MVP; replace with proper persistence later)
_jobs: dict[str, dict[str, Any]] = {}

from pipeline.single_pass import run as run_single_pass
from pipeline.types import Chapter


class RecognizeRequest(BaseModel):
    """Request body for starting role recognition."""

    # LLM config
    provider: str  # openai_compat | anthropic
    base_url: str
    api_key: str
    model: str
    temperature: float = 0.3
    max_tokens: int = 4096

    # Pipeline config
    mode: str = "single_pass"  # single_pass | two_pass

    # Chapters to process
    chapters: list[dict]  # [{index, title, text}, ...]


@router.post("/recognize")
async def recognize(req: RecognizeRequest) -> dict:
    """Start a recognition job. Returns job_id immediately; progress via WebSocket."""
    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = {"status": "queued", "results": None, "error": None}
    return {"job_id": job_id}


@router.websocket("/stream/{job_id}")
async def stream_progress(websocket: WebSocket, job_id: str) -> None:
    """WebSocket: run recognition pipeline and stream progress live."""
    await websocket.accept()

    if job_id not in _jobs:
        await websocket.send_json({"type": "error", "message": "Unknown job_id"})
        await websocket.close()
        return

    # In a real system the job would already be queued by the POST handler.
    # For MVP simplicity, we run it here and stream events.
    # The client sends the full request via the first WebSocket message.
    try:
        # Wait for the client to send the config + chapters
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=30)
        req = RecognizeRequest(**json.loads(raw))
    except (asyncio.TimeoutError, json.JSONDecodeError, ValueError) as exc:
        await websocket.send_json({"type": "error", "message": f"Invalid request: {exc}"})
        await websocket.close()
        return

    config = LLMConfig(
        provider=req.provider,
        base_url=req.base_url,
        api_key=req.api_key,
        model=req.model,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
    )
    client = create_client(config)

    chapters = [
        Chapter(index=c["index"], title=c["title"], text=c["text"]) for c in req.chapters
    ]

    async def on_progress(event: dict[str, Any]) -> None:
        await websocket.send_json(event)

    _jobs[job_id]["status"] = "running"
    await websocket.send_json(make_event("pipeline_start", total_chapters=len(chapters), mode=req.mode))

    try:
        if req.mode == "single_pass":
            results, roles = await run_single_pass(chapters, client, config, on_progress)
        elif req.mode == "two_pass":
            from pipeline.two_pass import run as run_two_pass

            results, roles = await run_two_pass(chapters, client, config, on_progress)
        else:
            await websocket.send_json(
                {"type": "error", "message": f"Unknown mode: {req.mode}. Use single_pass or two_pass"}
            )
            await websocket.close()
            return

        await websocket.send_json(
            {
                "type": "pipeline_done",
                "total_chapters": len(chapters),
                "results": [
                    {
                        "chapter_index": r.chapter_index,
                        "sml": r.sml,
                        "roles_appeared": r.roles_appeared,
                    }
                    for r in results
                ],
                "roles": [
                    {
                        "name": role.name,
                        "gender": role.gender,
                        "age": role.age,
                        "aliases": role.aliases,
                        "role": role.role,
                    }
                    for role in roles
                ],
            }
        )
        _jobs[job_id]["status"] = "done"

    except Exception as exc:
        _jobs[job_id]["status"] = "error"
        _jobs[job_id]["error"] = str(exc)
        # Fix #3: sanitize error message to avoid leaking API keys
        safe_msg = _sanitize_error(str(exc))
        await websocket.send_json({"type": "error", "message": safe_msg})

    await websocket.close()
