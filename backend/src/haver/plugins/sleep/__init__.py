"""The sleep domain."""

from pathlib import Path

import psycopg

from haver.core.plugin import Plugin
from haver.core.tools import Tool
from haver.plugins.sleep.log import SCHEMA, sleep_tool


def _tools(conn: psycopg.Connection) -> list[Tool]:
    return [sleep_tool(conn)]


PLUGIN = Plugin(
    name="sleep", knowledge_dir=Path(__file__).parent / "knowledge", tools=_tools, schema=SCHEMA
)
