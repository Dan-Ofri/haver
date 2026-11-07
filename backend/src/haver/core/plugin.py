"""The one interface through which a domain plugs into the core."""

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import psycopg

from haver.core.embedding import Embedder
from haver.core.knowledge import search_tool
from haver.core.memory import remember_tool
from haver.core.safety import RedFlag
from haver.core.tools import RESPOND, Tool


def _no_tools(conn: psycopg.Connection) -> list[Tool]:
    return []


@dataclass(frozen=True)
class Plugin:
    """A domain: its knowledge documents and its tools.

    `tools` gets a database connection per request and returns the domain's tools.
    """

    name: str
    knowledge_dir: Path | None = None
    tools: Callable[[psycopg.Connection], list[Tool]] = field(default=_no_tools)
    red_flags: list[RedFlag] = field(default_factory=list)


def knowledge_dirs(plugins: list[Plugin]) -> list[Path]:
    return [p.knowledge_dir for p in plugins if p.knowledge_dir is not None]


def all_red_flags(plugins: list[Plugin]) -> list[RedFlag]:
    return [flag for plugin in plugins for flag in plugin.red_flags]


def all_tools(conn: psycopg.Connection, plugins: list[Plugin], embedder: Embedder) -> list[Tool]:
    """Every tool the agent gets: the core's (search, memory), then each plugin's."""
    tools = [search_tool(conn, embedder), remember_tool(conn)] + [
        tool for plugin in plugins for tool in plugin.tools(conn)
    ]
    names = [tool.name for tool in tools]
    clashes = sorted({n for n in names if names.count(n) > 1 or n == RESPOND})
    if clashes:
        raise ValueError(f"tool names must be unique and not 'respond': {clashes}")
    return tools
