from pathlib import Path

import psycopg
import pytest

from haver.core import knowledge
from haver.main import KNOWLEDGE_DIR


def test_every_shipped_document_parses() -> None:
    docs = [knowledge.parse_document(p) for p in sorted(KNOWLEDGE_DIR.glob("*.md"))]
    assert len(docs) >= 5
    assert all(d.url.startswith("https://") and d.body for d in docs)


def test_rejects_a_document_without_a_source(tmp_path: Path) -> None:
    path = tmp_path / "bad.md"
    path.write_text("# Title\nNo source line\nBody")
    with pytest.raises(ValueError, match="Source"):
        knowledge.parse_document(path)


def test_finds_the_relevant_document(conn: psycopg.Connection) -> None:
    knowledge.load(conn, KNOWLEDGE_DIR)
    results = knowledge.search(conn, "How much protein do I need to build muscle?")
    assert results[0].id == "protein-for-muscle-gain"


def test_finds_nothing_for_an_unrelated_or_empty_query(conn: psycopg.Connection) -> None:
    knowledge.load(conn, KNOWLEDGE_DIR)
    assert knowledge.search(conn, "keto recipe for dinner") == []
    assert knowledge.search(conn, "the and of") == []


def test_loading_twice_does_not_duplicate(conn: psycopg.Connection) -> None:
    first = knowledge.load(conn, KNOWLEDGE_DIR)
    knowledge.load(conn, KNOWLEDGE_DIR)
    assert conn.execute("SELECT count(*) FROM documents").fetchone() == (first,)
