"""EPUB and TXT chapter parser — self-contained, no dependency on ebook2audiobook.

Uses ebooklib directly for EPUB parsing. This replaces the previous
approach of importing lib.core from ebook2audiobook, which had heavy
transitive dependencies (torch, gradio, coqui-tts, etc).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


def parse_epub_chapters(epub_path: str) -> list[dict]:
    """Parse an EPUB file and return chapter text blocks.

    Uses ebooklib to follow the spine, extracting headings as chapter titles
    and paragraph text as chapter content.

    Returns:
        [{"index": 0, "title": "...", "text": "..."}]
    """
    from ebooklib import epub, ITEM_DOCUMENT
    from lxml import html as lxml_html

    book = epub.read_epub(epub_path)
    chapters = []

    # Follow spine order for correct chapter sequence
    spine_items = []
    for item in book.spine:
        # spine entries are (idref, linear) tuples or just idref
        href = item[0] if isinstance(item, (list, tuple)) else item
        spine_item = book.get_item_with_href(href)
        if spine_item is not None:
            spine_items.append(spine_item)

    # Fallback: if spine parsing yields nothing, use all documents
    if not spine_items:
        spine_items = list(book.get_items_of_type(ITEM_DOCUMENT))

    idx = 0
    for item in spine_items:
        try:
            tree = lxml_html.fromstring(item.get_content())
        except Exception:
            continue

        # Extract chapter title from first heading
        title_els = tree.xpath("//h1 | //h2 | //h3")
        ch_title = title_els[0].text_content().strip() if title_els else f"Chapter {idx + 1}"

        # Extract all paragraph text
        paragraphs = tree.xpath("//p")
        if paragraphs:
            text_parts = [p.text_content().strip() for p in paragraphs]
        else:
            # Fallback: get all text from body
            body = tree.xpath("//body")
            text_parts = [body[0].text_content().strip()] if body else []

        full_text = "\n".join(t for t in text_parts if t)

        if full_text:
            chapters.append({"index": idx, "title": ch_title, "text": full_text})
            idx += 1

    return chapters


def parse_txt_chapters(text_path: str, encoding: str = "utf-8") -> list[dict]:
    """Parse a plain text file into chapters.

    Splits by common Chinese chapter heading patterns:
    - 第X章 / 第X回 / 第X节
    - Chapter N (English)
    """
    content = Path(text_path).read_text(encoding=encoding)

    # Common Chinese chapter heading patterns
    pattern = re.compile(
        r"^(第[一二三四五六七八九十百千零\d]+[章回节卷篇话幕].*?)$",
        re.MULTILINE,
    )

    matches = list(pattern.finditer(content))

    if not matches:
        # No chapter headings found — treat as single chapter
        return [{"index": 0, "title": "全文", "text": content.strip()}]

    chapters = []
    for i, match in enumerate(matches):
        ch_title = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        ch_text = content[start:end].strip()
        if ch_text:
            chapters.append({"index": i, "title": ch_title, "text": ch_text})

    return chapters
