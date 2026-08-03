"""Book import and chapter parsing endpoints."""

from __future__ import annotations

import logging
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from e2a.parser import parse_epub_chapters, parse_txt_chapters

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_UPLOAD_MB = 100
ALLOWED_SUFFIXES = {".epub", ".txt", ".mobi", ".azw3", ".pdf", ".docx", ".doc", ".html", ".rtf"}


class BookPreview(BaseModel):
    filename: str
    title: str = ""
    total_chapters: int
    chapters: list[dict]  # [{index, title, text_preview, char_count}]


def _sanitize_filename(filename: str) -> str:
    """Strip path components, keep only the base name + safe chars."""
    base = Path(filename).name  # strips ../../ etc
    safe = "".join(c for c in base if c.isalnum() or c in "._-")
    return safe or "upload"


@router.post("/import", response_model=BookPreview)
async def import_book(file: UploadFile = File(...)) -> BookPreview:
    """Import a TXT/EPUB file, parse chapters, return preview."""
    raw_name = file.filename or "upload"
    suffix = Path(raw_name).suffix.lower()

    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(400, f"Unsupported file type: {suffix}. Allowed: {ALLOWED_SUFFIXES}")

    # Read with size limit (fix #4: OOM protection)
    content = await file.read()
    if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File too large. Max {MAX_UPLOAD_MB}MB")

    if not content:
        raise HTTPException(400, "Empty file")

    # Fix #1: sanitized filename, random temp dir
    safe_name = _sanitize_filename(raw_name)
    tmp_dir = Path(tempfile.mkdtemp(prefix=f"audiobook_{uuid.uuid4().hex[:8]}_"))
    saved_path = tmp_dir / f"{safe_name}{suffix}"
    saved_path.write_bytes(content)

    try:
        if suffix == ".epub":
            chapters = parse_epub_chapters(str(saved_path))
            title = Path(safe_name).stem
        elif suffix == ".txt":
            encoding = "utf-8"
            try:
                content.decode("utf-8")
            except UnicodeDecodeError:
                encoding = "gbk"
            text_data = content.decode(encoding, errors="replace")
            text_path = tmp_dir / "upload.txt"
            text_path.write_text(text_data, encoding="utf-8")
            chapters = parse_txt_chapters(str(text_path))
            title = Path(safe_name).stem
        else:
            # Other formats need Calibre ebook-convert (future)
            raise HTTPException(
                400,
                f"Format {suffix} not yet supported. Convert to EPUB or TXT first. "
                f"Calibre integration pending.",
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Parse failed for %s: %s", safe_name, exc)
        raise HTTPException(422, f"Failed to parse file: {exc}")

    if not chapters:
        raise HTTPException(422, "No chapters found in file")

    # Build preview (truncate text for display)
    preview_chapters = []
    for ch in chapters[:20]:
        preview_chapters.append({
            "index": ch["index"],
            "title": ch["title"],
            "text_preview": ch["text"][:500] + ("..." if len(ch["text"]) > 500 else ""),
            "char_count": len(ch["text"]),
        })

    return BookPreview(
        filename=safe_name,
        title=title,
        total_chapters=len(chapters),
        chapters=preview_chapters,
    )
