"""Voice assignment endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from tts.factory import ENGINE_METADATA, ENGINE_CONFIG_FIELDS

router = APIRouter()


@router.get("/engines")
async def list_tts_engines() -> dict:
    """List available TTS engines with metadata. Single source of truth."""
    return {
        "engines": ENGINE_METADATA,
        "config_fields": ENGINE_CONFIG_FIELDS,
    }
