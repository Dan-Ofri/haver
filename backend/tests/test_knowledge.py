from pathlib import Path

import psycopg
import pytest

from haver.core import knowledge
from haver.core.plugin import knowledge_dirs
from haver.plugins import PLUGINS

DIRS = knowledge_dirs(PLUGINS)


def test_every_shipped_document_parses() -> None:
    docs = [knowledge.parse_document(p) for d in DIRS for p in sorted(d.glob("*.md"))]
    assert len(docs) >= 5
    assert all(d.url.startswith("https://") and d.body for d in docs)


def test_rejects_a_document_without_a_source(tmp_path: Path) -> None:
    path = tmp_path / "bad.md"
    path.write_text("# Title\nNo source line\nBody")
    with pytest.raises(ValueError, match="Source"):
        knowledge.parse_document(path)


def test_finds_the_relevant_document(conn: psycopg.Connection) -> None:
    knowledge.load(conn, DIRS)
    results = knowledge.search(conn, "How much protein do I need to build muscle?")
    assert results[0].id == "protein-for-muscle-gain"


def test_finds_nothing_for_an_unrelated_or_empty_query(conn: psycopg.Connection) -> None:
    knowledge.load(conn, DIRS)
    assert knowledge.search(conn, "keto recipe for dinner") == []
    assert knowledge.search(conn, "the and of") == []


def test_loading_twice_does_not_duplicate(conn: psycopg.Connection) -> None:
    first = knowledge.load(conn, DIRS)
    knowledge.load(conn, DIRS)
    assert conn.execute("SELECT count(*) FROM documents").fetchone() == (first,)


def test_rejects_duplicate_ids_across_plugins(tmp_path: Path, conn: psycopg.Connection) -> None:
    for folder in ("a", "b"):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "same.md").write_text("# T\nSource: https://x.org\nBody")
    with pytest.raises(ValueError, match="duplicate"):
        knowledge.load(conn, [tmp_path / "a", tmp_path / "b"])
