"""HTTP entry point."""

import logging
import threading
from typing import Literal

import psycopg
from fastapi import FastAPI
from pydantic import BaseModel, Field

from haver import db
from haver.config import Settings, get_settings
from haver.core import knowledge
from haver.core.agent import AgentResult, run_agent
from haver.core.llm import LLM
from haver.core.plugin import Plugin, knowledge_dirs
from haver.plugins import PLUGINS
from haver.providers import build_llm

logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: Literal["ok"]
    database: Literal["ok", "unavailable"]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


def create_app(
    settings: Settings | None = None, llm: LLM | None = None, plugins: list[Plugin] = PLUGINS
) -> FastAPI:
    settings = settings or get_settings()
    model = llm or build_llm(settings)

    loaded = False
    lock = threading.Lock()

    def ensure_knowledge(conn: psycopg.Connection) -> None:
        # Loaded on first use rather than at startup, so a database that starts late still works.
        # The lock keeps concurrent first requests from creating the schema twice.
        nonlocal loaded
        with lock:
            if not loaded:
                count = knowledge.load(conn, knowledge_dirs(plugins))
                logger.info("Loaded %d knowledge documents", count)
                loaded = True

    app = FastAPI(title="Haver API", version="0.1.0")

    @app.get("/api/health")
    def health() -> HealthResponse:
        database = "ok" if db.ping(settings.database_url) else "unavailable"
        return HealthResponse(status="ok", database=database)

    @app.post("/api/chat")
    def chat(request: ChatRequest) -> AgentResult:
        with psycopg.connect(settings.database_url, connect_timeout=5) as conn:
            ensure_knowledge(conn)
            tools = [knowledge.search_tool(conn)] + [t for p in plugins for t in p.tools(conn)]
            return run_agent(model, tools, request.message)

    return app


app = create_app()
