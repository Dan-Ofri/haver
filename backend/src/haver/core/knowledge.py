"""The knowledge base: documents loaded from Markdown files, found by hybrid search.

Hybrid search merges two rankings with reciprocal rank fusion: full-text search (exact words,
such as exercise names) and vector search (meaning, and languages the text search does not stem).
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path

import psycopg
from pydantic import BaseModel, Field

from haver.core.embedding import DIMENSIONS, Embedder
from haver.core.tools import Source, Tool, ToolOutput

# Each ranking contributes its top results; 60 is the standard damping constant for fusion.
CANDIDATES = 10
RRF_K = 60

SCHEMA = f"""
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS documents (
    id text PRIMARY KEY,
    title text NOT NULL,
    url text NOT NULL,
    body text NOT NULL,
    search tsvector GENERATED ALWAYS AS (
        to_tsvector('english', title || ' ' || body)
    ) STORED,
    content_hash text NOT NULL DEFAULT '',
    embedding_model text,
    embedding vector({DIMENSIONS})
);
CREATE INDEX IF NOT EXISTS documents_search_idx ON documents USING gin (search);
"""


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    url: str
    body: str

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(f"{self.title}\n{self.body}".encode()).hexdigest()


def parse_document(path: Path) -> Document:
    """A document is a Markdown file: '# Title', then 'Source: URL', then the body."""
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    if len(lines) < 3 or not lines[0].startswith("# ") or not lines[1].startswith("Source: "):
        raise ValueError(f"{path.name}: expected '# Title' and 'Source: URL' on the first lines")
    return Document(
        id=path.stem,
        title=lines[0].removeprefix("# ").strip(),
        url=lines[1].removeprefix("Source: ").strip(),
        body="\n".join(lines[2:]).strip(),
    )


def _literal(vector: list[float]) -> str:
    return "[" + ",".join(repr(x) for x in vector) + "]"


def load(conn: psycopg.Connection, folders: list[Path], embedder: Embedder) -> int:
    """Create the schema and upsert every document. Returns the count.

    A document is embedded again only when its text or the embedding model changed.
    """
    documents = [parse_document(p) for folder in folders for p in sorted(folder.glob("*.md"))]
    ids = [doc.id for doc in documents]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise ValueError(f"duplicate document IDs across plugins: {duplicates}")
    with conn.transaction():
        conn.execute(SCHEMA)
        known = {
            row[0]: (row[1], row[2])
            for row in conn.execute("SELECT id, content_hash, embedding_model FROM documents")
        }
        stale = [d for d in documents if known.get(d.id) != (d.content_hash, embedder.name)]
        vectors = embedder.embed([f"{d.title}\n{d.body}" for d in stale])
        by_id = {d.id: _literal(v) for d, v in zip(stale, vectors, strict=True)}
        for doc in documents:
            conn.execute(
                """
                INSERT INTO documents (id, title, url, body, content_hash)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET title = EXCLUDED.title, url = EXCLUDED.url,
                    body = EXCLUDED.body, content_hash = EXCLUDED.content_hash
                """,
                (doc.id, doc.title, doc.url, doc.body, doc.content_hash),
            )
            if doc.id in by_id:
                conn.execute(
                    "UPDATE documents SET embedding = %s::vector, embedding_model = %s "
                    "WHERE id = %s",
                    (by_id[doc.id], embedder.name, doc.id),
                )
    return len(documents)


def _keyword_ids(conn: psycopg.Connection, query: str) -> list[str]:
    rows = conn.execute(
        """
        WITH q AS (
            SELECT nullif(replace(plainto_tsquery('english', %s)::text, '&', '|'), '')::tsquery
                AS query
        )
        SELECT id FROM documents, q
        WHERE search @@ q.query
        ORDER BY ts_rank_cd(search, q.query) DESC, id
        LIMIT %s
        """,
        (query, CANDIDATES),
    ).fetchall()
    return [row[0] for row in rows]


def _vector_ids(conn: psycopg.Connection, query: str, embedder: Embedder) -> list[str]:
    [vector] = embedder.embed([query])
    if not any(vector):  # a query with nothing to embed has no direction, so nothing is close
        return []
    rows = conn.execute(
        """
        SELECT id FROM documents
        WHERE embedding_model = %(model)s AND 1 - (embedding <=> %(v)s::vector) >= %(min)s
        ORDER BY embedding <=> %(v)s::vector, id
        LIMIT %(n)s
        """,
        {
            "model": embedder.name,
            "v": _literal(vector),
            "min": embedder.min_similarity,
            "n": CANDIDATES,
        },
    ).fetchall()
    return [row[0] for row in rows]


def fuse(rankings: list[list[str]]) -> list[str]:
    """Reciprocal rank fusion: a document scores 1/(k+rank) in each ranking it appears in."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1 / (RRF_K + rank)
    return sorted(scores, key=lambda i: (-scores[i], i))


def search(
    conn: psycopg.Connection, query: str, embedder: Embedder, limit: int = 3
) -> list[Document]:
    """The best documents for the query by keywords and by meaning, merged."""
    ids = fuse([_keyword_ids(conn, query), _vector_ids(conn, query, embedder)])[:limit]
    if not ids:
        return []
    rows = conn.execute(
        "SELECT id, title, url, body FROM documents WHERE id = ANY(%s)", (ids,)
    ).fetchall()
    found = {row[0]: Document(*row) for row in rows}
    return [found[i] for i in ids]


class SearchArgs(BaseModel):
    query: str = Field(min_length=1, max_length=2000, description="What to look up.")


def search_tool(conn: psycopg.Connection, embedder: Embedder) -> Tool:
    def run(args: SearchArgs) -> ToolOutput:
        docs = search(conn, args.query, embedder)
        if not docs:
            return ToolOutput(content="No documents found.")
        content = "\n\n".join(
            f'<document id="{d.id}" title="{d.title}">\n{d.body}\n</document>' for d in docs
        )
        return ToolOutput(
            content=content,
            sources=[Source(id=d.id, title=d.title, url=d.url) for d in docs],
        )

    return Tool(
        name="search_knowledge",
        description="Search the coaching knowledge base by keywords and by meaning.",
        args_model=SearchArgs,
        run=run,
    )
