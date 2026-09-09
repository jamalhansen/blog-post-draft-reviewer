"""Tests for context retrieval via vsearch in blog-post-draft-reviewer."""

import sqlite3
from pathlib import Path

import pytest

from reviewer.context import (
    extract_search_terms,
    format_discovery_context,
    format_vault_context,
    get_discovery_context,
    get_vault_context,
)


@pytest.fixture
def mock_bm25_db(tmp_path):
    db_file = tmp_path / "bm25.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("""
        CREATE VIRTUAL TABLE chunks_fts USING fts5(
            chunk_id UNINDEXED,
            source_file,
            breadcrumb,
            chunk_index UNINDEXED,
            content,
            tokenize = 'porter unicode61'
        );
    """)
    conn.execute(
        "INSERT INTO chunks_fts VALUES (?, ?, ?, ?, ?)",
        (
            "sql-intro.md::chunk::0",
            "sql-intro.md",
            "SQL Basics",
            0,
            "In this series we cover Python and SQL, focusing on NULL value semantics.",
        ),
    )
    conn.execute(
        "INSERT INTO chunks_fts VALUES (?, ?, ?, ?, ?)",
        (
            "current_post.md::chunk::0",
            "current_post.md",
            "Current",
            0,
            "This is the current post being reviewed about SQL NULL values.",
        ),
    )
    conn.commit()
    conn.close()
    return db_file


class TestExtractSearchTerms:
    def test_extracts_title_and_paragraph(self):
        title = "Understanding SQL NULL Values"
        content = "# Heading\n\nFirst paragraph with some key explanation about databases."
        terms = extract_search_terms(title, content)
        assert "Understanding SQL NULL Values" in terms
        assert "First paragraph" in terms

    def test_skips_untitled(self):
        terms = extract_search_terms("(untitled)", "Just content here.")
        assert "(untitled)" not in terms
        assert "Just content" in terms


class TestGetVaultContext:
    def test_returns_empty_if_db_missing(self, tmp_path):
        results = get_vault_context("test", "content", db_path=tmp_path / "missing.db")
        assert results == []

    def test_retrieves_relevant_chunks(self, mock_bm25_db):
        results = get_vault_context(
            "SQL NULL semantics",
            "We are exploring how SQL handles nulls.",
            db_path=mock_bm25_db,
        )
        assert len(results) > 0
        assert results[0]["source_file"] in {"sql-intro.md", "current_post.md"}

    def test_excludes_current_file(self, mock_bm25_db):
        results = get_vault_context(
            "SQL NULL semantics",
            "We are exploring how SQL handles nulls.",
            current_file=Path("path/to/current_post.md"),
            db_path=mock_bm25_db,
        )
        # current_post.md should be excluded
        for r in results:
            assert r["source_file"] != "current_post.md"
        assert any(r["source_file"] == "sql-intro.md" for r in results)


class TestFormatVaultContext:
    def test_empty_returns_empty(self):
        assert format_vault_context([]) == ""

    def test_formats_items(self):
        items = [
            {
                "source_file": "notes/sql.md",
                "breadcrumb": "NULL section",
                "snippet": "Snippet content here",
            }
        ]
        formatted = format_vault_context(items)
        assert "notes/sql.md" in formatted
        assert "NULL section" in formatted
        assert "Snippet content here" in formatted


class TestGetDiscoveryContext:
    def test_returns_empty_if_db_missing(self, tmp_path):
        results = get_discovery_context("title", "content", db_path=tmp_path / "missing.db")
        assert results == []

    def test_retrieves_matching_kept_articles(self, tmp_path):
        db_file = tmp_path / "content-discovery.db"
        conn = sqlite3.connect(str(db_file))
        conn.execute("""
            CREATE TABLE items (
                id INTEGER PRIMARY KEY,
                url TEXT,
                title TEXT,
                source TEXT,
                tags TEXT,
                summary TEXT,
                description TEXT,
                status TEXT,
                reviewed_at TEXT
            );
        """)
        conn.execute(
            "INSERT INTO items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                1,
                "https://sqlite.org/arch",
                "SQLite Architecture Insights",
                "feed",
                '["sqlite", "database"]',
                "Deep dive into SQLite storage engine.",
                "",
                "kept",
                "2026-09-01",
            ),
        )
        conn.execute(
            "INSERT INTO items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                2,
                "https://css.org/flexbox",
                "Flexbox layout guide",
                "feed",
                '["css"]',
                "CSS tips",
                "",
                "kept",
                "2026-09-01",
            ),
        )
        conn.commit()
        conn.close()

        results = get_discovery_context(
            "Understanding SQLite Architecture",
            "This post explores how SQLite works internally.",
            db_path=db_file,
        )
        assert len(results) == 1
        assert results[0]["title"] == "SQLite Architecture Insights"
        assert "sqlite" in results[0]["tags"]


class TestFormatDiscoveryContext:
    def test_empty_returns_empty(self):
        assert format_discovery_context([]) == ""

    def test_formats_items_with_tags(self):
        items = [
            {
                "title": "SQLite Internals",
                "url": "https://sqlite.org",
                "tags": ["sqlite", "offline"],
                "summary": "Storage details.",
            }
        ]
        formatted = format_discovery_context(items)
        assert "[SQLite Internals](https://sqlite.org)" in formatted
        assert "[#sqlite, #offline]" in formatted
        assert "Storage details." in formatted

