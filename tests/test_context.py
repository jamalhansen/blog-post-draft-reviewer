"""Tests for context retrieval via vsearch in blog-post-draft-reviewer."""

import sqlite3
from pathlib import Path

import pytest

from reviewer.context import (
    extract_search_terms,
    format_vault_context,
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
