"""Context retrieval for blog-post-draft-reviewer via vsearch."""

from __future__ import annotations

import json
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


def get_discovery_db_path() -> Path:
    """Return path to content-discovery SQLite database."""
    env = os.environ.get("CONTENT_DISCOVERY_STORE") or os.environ.get("CONTENT_DISCOVERY_DB")
    if env:
        return Path(os.path.expanduser(env))
    return Path.home() / ".content-discovery.db"


def get_discovery_context(
    title: str,
    content: str,
    top_k: int = 3,
    db_path: Optional[Path] = None,
) -> list[dict]:
    """Retrieve relevant kept research items from content-discovery archive."""
    path = db_path or get_discovery_db_path()
    if not path.exists():
        return []

    search_text = extract_search_terms(title, content)
    if not search_text:
        return []

    words = [w.lower() for w in re.findall(r"\b[A-Za-z]{4,}\b", search_text)[:15]]
    if not words:
        return []

    try:
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT title, url, summary, source, tags, description
            FROM items
            WHERE status = 'kept'
            ORDER BY reviewed_at DESC
            """
        ).fetchall()
        conn.close()
    except Exception:
        return []

    matched: list[dict] = []
    for r in rows:
        item = dict(r)
        item_tags: list[str] = []
        try:
            item_tags = [
                str(t).strip().lower()
                for t in json.loads(item.get("tags") or "[]")
            ]
        except (json.JSONDecodeError, TypeError):
            pass
        searchable = " ".join([
            item.get("title") or "",
            item.get("summary") or "",
            item.get("description") or "",
            item.get("source") or "",
            " ".join(item_tags),
        ]).lower()

        overlap = sum(1 for w in words if w in searchable)
        if overlap > 0:
            matched.append(
                {
                    "title": item.get("title") or "",
                    "url": item.get("url") or "",
                    "summary": item.get("summary") or item.get("description") or "",
                    "tags": item_tags,
                    "score": overlap,
                }
            )

    matched.sort(key=lambda x: x["score"], reverse=True)
    return matched[:top_k]


def format_discovery_context(items: list[dict]) -> str:
    """Format discovery context items into prompt markdown."""
    if not items:
        return ""
    lines = []
    for i, item in enumerate(items, start=1):
        tag_str = f" [#{', #'.join(item['tags'])}]" if item.get("tags") else ""
        lines.append(f"{i}. [{item['title']}]({item['url']}){tag_str}\n   \"{item['summary']}\"")
    return "\n\n".join(lines)

