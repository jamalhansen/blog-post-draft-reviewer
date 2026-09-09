"""Context retrieval for blog-post-draft-reviewer via vsearch."""

from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from typing import Optional


def get_vsearch_db_path() -> Path:
    """Return path to vsearch SQLite BM25 database."""
    xdg_data = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    return Path(xdg_data) / "vsearch" / "bm25.db"


def extract_search_terms(title: str, content: str) -> str:
    """Extract key terms from title and first paragraph for search."""
    terms = []
    if title and title != "(untitled)":
        terms.append(title)
    # Extract first non-heading paragraph
    for para in content.split("\n\n"):
        stripped = para.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("---"):
            clean = re.sub(r"[#*_`\[\]()]", " ", stripped)
            words = clean.split()[:20]
            terms.append(" ".join(words))
            break
    return " ".join(terms)


def get_vault_context(
    title: str,
    content: str,
    current_file: Optional[Path | str] = None,
    top_k: int = 3,
    db_path: Optional[Path] = None,
) -> list[dict]:
    """Retrieve related chunks from the vault for background context."""
    path = db_path or get_vsearch_db_path()
    if not path.exists():
        return []

    search_text = extract_search_terms(title, content)
    if not search_text:
        return []

    tokens = re.findall(r'\"([^\"]+)\"|(\w+)', search_text)
    terms: list[str] = []
    for phrase, word in tokens:
        if phrase:
            clean = " ".join(re.findall(r"\w+", phrase))
            if clean:
                terms.append(f'"{clean}"')
        elif word and len(word) > 2:
            terms.append(f'"{word}"')
    if not terms:
        return []

    fts_query = " OR ".join(terms[:15])

    current_name = Path(current_file).name if current_file else None
    results: list[dict] = []

    try:
        conn = sqlite3.connect(str(path))
        sql = """
            SELECT chunk_id, source_file, breadcrumb, content, bm25(chunks_fts) as rank
            FROM chunks_fts
            WHERE chunks_fts MATCH ?
            ORDER BY rank ASC
            LIMIT ?
        """
        cursor = conn.execute(sql, (fts_query, top_k * 3))
        rows = cursor.fetchall()
        conn.close()
    except Exception:
        return []

    for _, source_file, breadcrumb, text, rank in rows:
        if current_name and (current_name in source_file or source_file in str(current_file)):
            continue
        snippet = " ".join(text.strip().split())
        if len(snippet) > 250:
            snippet = snippet[:250].rsplit(" ", 1)[0] + "…"
        results.append(
            {
                "source_file": source_file,
                "breadcrumb": breadcrumb,
                "snippet": snippet,
                "score": -float(rank),
            }
        )
        if len(results) >= top_k:
            break

    return results


def format_vault_context(context_items: list[dict]) -> str:
    """Format retrieved vault chunks into prompt markdown."""
    if not context_items:
        return ""
    lines = []
    for i, item in enumerate(context_items, start=1):
        src = item["source_file"]
        bc = f" (Section: {item['breadcrumb']})" if item.get("breadcrumb") else ""
        lines.append(f"{i}. Note: `{src}`{bc}\n   \"{item['snippet']}\"")
    return "\n\n".join(lines)
