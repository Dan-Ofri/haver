"""The knowledge base: documents loaded from Markdown files, searched with full-text search.

Phase 2 uses keyword search only. Hybrid search with embeddings replaces it in phase 3.
"""

from dataclasses import dataclass
from pathlib import Path

import psycopg
from pydantic import BaseModel, Field

from haver.core.tools import Source, Tool, ToolOutput

KNOWLEDGE_DIR = Path(__file__).parents[1] / "knowledge"

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id text PRIMARY KEY,
    title text NOT NULL,
    url text NOT NULL,
    body text NOT NULL,
    search tsvector GENERATED ALWAYS AS (
        to_tsvector('english', title || ' ' || body)
    ) STORED
);
CREATE INDEX IF NOT EXISTS documents_search_idx ON documents USING gin (search);
"""


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    url: str
    body: str


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


def load(conn: psycopg.Connection, folder: Path) -> int:
    """Create the schema and upsert every document in the folder. Returns the count."""
    documents = [parse_document(path) for path in sorted(folder.glob("*.md"))]
    with conn.transaction():
        conn.execute(SCHEMA)
        for doc in documents:
            conn.execute(
                """
                INSERT INTO documents (id, title, url, body) VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE
                SET title = EXCLUDED.title, url = EXCLUDED.url, body = EXCLUDED.body
                """,
                (doc.id, doc.title, doc.url, doc.body),
            )
    return len(documents)


def search(conn: psycopg.Connection, query: str, limit: int = 3) -> list[Document]:
    """Rank documents that share any keyword with the query."""
    rows = conn.execute(
        """
        WITH q AS (
            SELECT nullif(replace(plainto_tsquery('english', %s)::text, '&', '|'), '')::tsquery
                AS query
        )
        SELECT id, title, url, body FROM documents, q
        WHERE search @@ q.query
        ORDER BY ts_rank_cd(search, q.query) DESC, id
        LIMIT %s
        """,
        (query, limit),
    ).fetchall()
    return [Document(*row) for row in rows]


class SearchArgs(BaseModel):
    query: str = Field(min_length=1, max_length=300, description="Keywords in English.")


def search_tool(conn: psycopg.Connection) -> Tool:
    def run(args: SearchArgs) -> ToolOutput:
        docs = search(conn, args.query)
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
        description="Search the coaching knowledge base. Use English keywords.",
        args_model=SearchArgs,
        run=run,
    )
