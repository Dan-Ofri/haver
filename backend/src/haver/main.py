"""HTTP entry point."""

import logging
import threading
from typing import Literal

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from haver import db
from haver.config import Settings, get_settings
from haver.core import knowledge, memory, safety
from haver.core.agent import AgentResult, run_agent
from haver.core.embedding import Embedder
from haver.core.llm import LLM
from haver.core.plugin import Plugin, all_red_flags, all_tools, knowledge_dirs
from haver.plugins import PLUGINS
from haver.providers import build_embedder, build_llm

logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: Literal["ok"]
    database: Literal["ok", "unavailable"]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


def create_app(
    settings: Settings | None = None,
    llm: LLM | None = None,
    plugins: list[Plugin] = PLUGINS,
    embedder: Embedder | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    model = llm or build_llm(settings)
    embedding = embedder or build_embedder(settings)

    loaded = False
    lock = threading.Lock()

    def ensure_knowledge(conn: psycopg.Connection) -> None:
        # Loaded on first use rather than at startup, so a database that starts late still works.
        # The lock keeps concurrent first requests from creating the schema twice.
        nonlocal loaded
        with lock:
            if not loaded:
                with conn.transaction():
                    memory.ensure_schema(conn)
                count = knowledge.load(conn, knowledge_dirs(plugins), embedding)
                logger.info("Loaded %d knowledge documents", count)
                loaded = True

    app = FastAPI(title="Haver API", version="0.1.0")

    @app.get("/api/health")
    def health() -> HealthResponse:
        database = "ok" if db.ping(settings.database_url) else "unavailable"
        return HealthResponse(status="ok", database=database)

    @app.post("/api/chat")
    def chat(request: ChatRequest) -> AgentResult:
        alert = safety.check(request.message, all_red_flags(plugins))
        if alert:
            return AgentResult(safety=alert)
        with psycopg.connect(settings.database_url, connect_timeout=5) as conn:
            ensure_knowledge(conn)
            return run_agent(
                model,
                all_tools(conn, plugins, embedding),
                request.message,
                memory=memory.prompt_block(memory.list_all(conn)),
            )

    @app.get("/api/memory")
    def list_memory() -> list[memory.Memory]:
        with psycopg.connect(settings.database_url, connect_timeout=5) as conn:
            ensure_knowledge(conn)
            return memory.list_all(conn)

    @app.post("/api/memory", status_code=201)
    def add_memory(body: memory.FactBody) -> memory.Memory:
        with psycopg.connect(settings.database_url, connect_timeout=5) as conn:
            ensure_knowledge(conn)
            try:
                return memory.add(conn, body.fact)
            except memory.MemoryFull:
                raise HTTPException(409, "Memory is full. Delete a fact first.") from None

    @app.put("/api/memory/{memory_id}")
    def edit_memory(memory_id: int, body: memory.FactBody) -> memory.Memory:
        with psycopg.connect(settings.database_url, connect_timeout=5) as conn:
            ensure_knowledge(conn)
            updated = memory.update(conn, memory_id, body.fact)
            if updated is None:
                raise HTTPException(404, "No such fact.")
            return updated

    @app.delete("/api/memory/{memory_id}", status_code=204)
    def forget(memory_id: int) -> None:
        with psycopg.connect(settings.database_url, connect_timeout=5) as conn:
            ensure_knowledge(conn)
            if not memory.delete(conn, memory_id):
                raise HTTPException(404, "No such fact.")

    return app


app = create_app()
