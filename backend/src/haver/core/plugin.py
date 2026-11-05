"""The one interface through which a domain plugs into the core."""

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import psycopg

from haver.core.knowledge import search_tool
from haver.core.tools import Tool


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


def knowledge_dirs(plugins: list[Plugin]) -> list[Path]:
    return [p.knowledge_dir for p in plugins if p.knowledge_dir is not None]


def all_tools(conn: psycopg.Connection, plugins: list[Plugin]) -> list[Tool]:
    """Every tool the agent gets: knowledge search from the core, then each plugin's tools."""
    return [search_tool(conn)] + [tool for plugin in plugins for tool in plugin.tools(conn)]
