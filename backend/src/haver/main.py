"""HTTP entry point."""

import logging
from pathlib import Path
from typing import Literal

import psycopg
from fastapi import FastAPI
from pydantic import BaseModel, Field

from haver import db
from haver.config import Settings, get_settings
from haver.core import knowledge
from haver.core.agent import AgentResult, run_agent
from haver.core.llm import LLM
from haver.providers import build_llm

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: Literal["ok"]
    database: Literal["ok", "unavailable"]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


def create_app(settings: Settings | None = None, llm: LLM | None = None) -> FastAPI:
    settings = settings or get_settings()
    model = llm or build_llm(settings)

    loaded = False

    def ensure_knowledge(conn: psycopg.Connection) -> None:
        # Loaded on first use rather than at startup, so a database that starts late still works.
        nonlocal loaded
        if not loaded:
            logger.info("Loaded %d knowledge documents", knowledge.load(conn, KNOWLEDGE_DIR))
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
            return run_agent(model, [knowledge.search_tool(conn)], request.message)

    return app


app = create_app()
