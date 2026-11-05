from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel

from haver.config import Settings
from haver.core.llm import LLMResponse, ToolCall
from haver.core.plugin import Plugin, all_tools
from haver.core.tools import Source, Tool, ToolOutput
from haver.main import create_app
from tests.fakes import ScriptedLLM


class NoArgs(BaseModel):
    pass


def streak_tool(conn: psycopg.Connection) -> list[Tool]:
    def run(_: NoArgs) -> ToolOutput:
        (count,) = conn.execute("SELECT count(*) FROM documents").fetchone() or (0,)
        return ToolOutput(
            content=f"{count} documents",
            sources=[Source(id="streak", title="Streak", url="https://example.org")],
        )

    return [Tool(name="streak", description="Test tool.", args_model=NoArgs, run=run)]


@pytest.fixture
def plugin(tmp_path: Path) -> Plugin:
    (tmp_path / "test-card.md").write_text("# Test card\nSource: https://example.org\nBody text")
    return Plugin(name="test", knowledge_dir=tmp_path, tools=streak_tool)


@pytest.fixture
def client(settings: Settings, conn: psycopg.Connection, plugin: Plugin) -> Iterator[TestClient]:
    llm = ScriptedLLM(
        LLMResponse(tool_calls=[ToolCall(id="1", name="streak", arguments={})]),
        LLMResponse(
            tool_calls=[
                ToolCall(
                    id="2",
                    name="respond",
                    arguments={"claims": [{"text": "One document.", "sources": ["streak"]}]},
                )
            ]
        ),
    )
    with TestClient(create_app(settings, llm=llm, plugins=[plugin])) as test_client:
        yield test_client


def test_a_plugin_adds_knowledge_and_tools_without_touching_the_core(
    client: TestClient, conn: psycopg.Connection
) -> None:
    body = client.post("/api/chat", json={"message": "streak?"}).json()
    assert body["steps"][0] == {
        "tool": "streak",
        "arguments": {},
        "ok": True,
        "detail": "1 result(s)",
    }
    assert body["claims"][0]["text"] == "One document."
    ids = [row[0] for row in conn.execute("SELECT id FROM documents").fetchall()]
    assert ids == ["test-card"]


def test_a_plugin_tool_cannot_take_a_reserved_or_used_name(conn: psycopg.Connection) -> None:
    respond_tool = Tool(
        name="respond", description="x", args_model=NoArgs, run=lambda _: ToolOutput(content="")
    )
    plugin = Plugin(name="bad", tools=lambda _conn: [respond_tool])
    with pytest.raises(ValueError, match="respond"):
        all_tools(conn, [plugin])
