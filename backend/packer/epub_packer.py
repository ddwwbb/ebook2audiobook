"""EPUB packer — rebuild an EPUB from SML-tagged chapter text.

Each chapter becomes an EpubHtml spine item. SML tags ([voice:角色名]...[/voice],
[pause:N], [break]) are preserved as plain text inside <p> tags.
A voices.json metadata file maps character names to voice configurations,
to be resolved at synthesis time.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from ebooklib import epub


def pack_epub(
    title: str,
    author: str = "",
    chapters: list[tuple[str, str]] | None = None,  # [(chapter_title, sml_text), ...]
    voices_map: dict | None = None,
    cover_path: str | None = None,
    output_path: str | None = None,
) -> str:
    """Create an EPUB from SML-tagged chapter text.

    Args:
        title: Book title.
        author: Author name.
        chapters: List of (title, sml_text) tuples.
        voices_map: {character_name: {engine, voice_id, ...}} for synthesis.
        cover_path: Path to cover image.
        output_path: Where to save the EPUB. If None, uses title.epub in cwd.

    Returns:
        Path to the created EPUB file.
    """
    book = epub.EpubBook()
    book.set_identifier(str(uuid.uuid4()))
    book.set_title(title)
    book.set_language("zh-CN")
    if author:
        book.add_author(author)

    # Cover
    if cover_path and Path(cover_path).exists():
        with open(cover_path, "rb") as f:
            cover_data = f.read()
        cover_img = epub.EpubItem(
            uid="cover_img",
            file_name="images/cover.jpg",
            media_type="image/jpeg",
            content=cover_data,
        )
        book.add_item(cover_img)
        book.set_cover("images/cover.jpg", cover_data)

    # Chapters
    chapters = chapters or []
    spine = ["nav"]
    toc = []

    for idx, (ch_title, sml_text) in enumerate(chapters):
        # Wrap each SML paragraph in <p> tags
        paragraphs = sml_text.strip().split("\n")
        html_body = "\n".join(f"<p>{p}</p>" for p in paragraphs if p.strip())

        chapter = epub.EpubHtml(
            title=ch_title,
            file_name=f"chap_{idx:03d}.xhtml",
            lang="zh-CN",
            content=f"<h1>{ch_title}</h1>\n{html_body}",
        )
        book.add_item(chapter)
        spine.append(chapter)
        toc.append(chapter)

    book.spine = spine
    book.toc = toc

    # Add NCX + nav
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Embed voices.json as a metadata item
    if voices_map:
        voices_json = epub.EpubItem(
            uid="voices_map",
            file_name="voices.json",
            media_type="application/json",
            content=json.dumps(voices_map, ensure_ascii=False, indent=2).encode("utf-8"),
        )
        book.add_item(voices_json)

    # Write
    if output_path is None:
        output_path = f"{title}.epub"

    epub.write_epub(output_path, book, {})
    return output_path
