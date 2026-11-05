from pathlib import Path

import psycopg
import pytest

from haver.core import knowledge
from haver.core.plugin import knowledge_dirs
from haver.plugins import PLUGINS
from haver.providers.offline_embedder import HashingEmbedder

DIRS = knowledge_dirs(PLUGINS)
EMBEDDER = HashingEmbedder()


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
    knowledge.load(conn, DIRS, EMBEDDER)
    results = knowledge.search(conn, "How much protein do I need to build muscle?", EMBEDDER)
    assert results[0].id == "protein-for-muscle-gain"


def test_finds_nothing_for_an_unrelated_or_empty_query(conn: psycopg.Connection) -> None:
    knowledge.load(conn, DIRS, EMBEDDER)
    assert knowledge.search(conn, "keto recipe for dinner", EMBEDDER) == []
    assert knowledge.search(conn, "the and of", EMBEDDER) == []


def test_loading_twice_does_not_duplicate(conn: psycopg.Connection) -> None:
    first = knowledge.load(conn, DIRS, EMBEDDER)
    knowledge.load(conn, DIRS, EMBEDDER)
    assert conn.execute("SELECT count(*) FROM documents").fetchone() == (first,)


def test_rejects_duplicate_ids_across_plugins(tmp_path: Path, conn: psycopg.Connection) -> None:
    for folder in ("a", "b"):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "same.md").write_text("# T\nSource: https://x.org\nBody")
    with pytest.raises(ValueError, match="duplicate"):
        knowledge.load(conn, [tmp_path / "a", tmp_path / "b"], EMBEDDER)


class CountingEmbedder(HashingEmbedder):
    def __init__(self, name: str = "counting") -> None:
        self.name = name
        self.embedded: list[str] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.embedded += texts
        return super().embed(texts)


def test_unchanged_documents_are_not_embedded_again(conn: psycopg.Connection) -> None:
    embedder = CountingEmbedder()
    count = knowledge.load(conn, DIRS, embedder)
    assert len(embedder.embedded) == count
    knowledge.load(conn, DIRS, embedder)
    assert len(embedder.embedded) == count


def test_a_changed_document_or_a_new_model_is_embedded_again(
    tmp_path: Path, conn: psycopg.Connection
) -> None:
    doc = tmp_path / "one.md"
    doc.write_text("# T\nSource: https://x.org\nfirst version")
    embedder = CountingEmbedder()
    knowledge.load(conn, [tmp_path], embedder)
    doc.write_text("# T\nSource: https://x.org\nsecond version")
    knowledge.load(conn, [tmp_path], embedder)
    assert len(embedder.embedded) == 2
    knowledge.load(conn, [tmp_path], CountingEmbedder("other-model"))
    row = conn.execute("SELECT embedding_model FROM documents").fetchone()
    assert row == ("other-model",)


def test_fusion_rewards_documents_found_by_both_rankings() -> None:
    assert knowledge.fuse([["a", "b", "c"], ["c", "d"]])[:2] == ["c", "a"]
    assert knowledge.fuse([[], []]) == []


class FixedEmbedder:
    """Puts every text on the same axis, except those containing 'zebra'."""

    name = "fixed"
    min_similarity = 0.5

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0, 1.0] + [0.0] * 766 if "zebra" in t else [1.0] + [0.0] * 767 for t in texts]


def test_vector_search_finds_a_document_with_no_shared_words(
    tmp_path: Path, conn: psycopg.Connection
) -> None:
    (tmp_path / "stripes.md").write_text("# Stripes\nSource: https://x.org\nzebra animal")
    (tmp_path / "other.md").write_text("# Other\nSource: https://x.org\nunrelated text")
    embedder = FixedEmbedder()
    knowledge.load(conn, [tmp_path], embedder)
    assert [d.id for d in knowledge.search(conn, "zebra", embedder)] == ["stripes"]
    assert [d.id for d in knowledge.search(conn, "אחר", embedder)] == ["other"]


def similarity(x: list[float], y: list[float]) -> float:
    return sum(i * j for i, j in zip(x, y, strict=True))


def test_hashing_embedder_ranks_shared_words_and_ignores_unrelated_text() -> None:
    a, b, c = EMBEDDER.embed(["protein muscle", "protein for muscle gain", "keto dinner"])
    assert similarity(a, b) > 0.7
    assert similarity(a, c) < EMBEDDER.min_similarity


def test_upgrades_a_table_from_before_embeddings(conn: psycopg.Connection) -> None:
    conn.execute(
        "CREATE TABLE documents (id text PRIMARY KEY, title text NOT NULL, url text NOT NULL,"
        " body text NOT NULL, search tsvector GENERATED ALWAYS AS"
        " (to_tsvector('english', title || ' ' || body)) STORED)"
    )
    knowledge.load(conn, DIRS, EMBEDDER)
    assert knowledge.search(conn, "protein muscle", EMBEDDER)


def test_never_embeds_an_empty_list(conn: psycopg.Connection) -> None:
    class Strict(CountingEmbedder):
        def embed(self, texts: list[str]) -> list[list[float]]:
            assert texts
            return super().embed(texts)

    embedder = Strict()
    knowledge.load(conn, DIRS, embedder)
    knowledge.load(conn, DIRS, embedder)


def test_a_document_with_no_vector_direction_is_not_returned(
    tmp_path: Path, conn: psycopg.Connection
) -> None:
    (tmp_path / "empty.md").write_text("# The\nSource: https://x.org\nthe and of")
    knowledge.load(conn, [tmp_path], EMBEDDER)
    assert knowledge.search(conn, "protein muscle", EMBEDDER) == []


def test_embeds_in_batches(tmp_path: Path, conn: psycopg.Connection) -> None:
    for i in range(120):
        (tmp_path / f"d{i}.md").write_text(f"# T{i}\nSource: https://x.org\nbody {i}")
    sizes: list[int] = []

    class Sizes(HashingEmbedder):
        def embed(self, texts: list[str]) -> list[list[float]]:
            sizes.append(len(texts))
            return super().embed(texts)

    knowledge.load(conn, [tmp_path], Sizes())
    assert sizes == [50, 50, 20]
