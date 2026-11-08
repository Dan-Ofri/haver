"""The training domain."""

from pathlib import Path

import psycopg

from haver.core.plugin import Plugin
from haver.core.tools import Tool
from haver.plugins.training.log import SCHEMA, workout_tool
from haver.plugins.training.red_flags import RED_FLAGS


def _tools(conn: psycopg.Connection) -> list[Tool]:
    return [workout_tool(conn)]


PLUGIN = Plugin(
    name="training",
    knowledge_dir=Path(__file__).parent / "knowledge",
    tools=_tools,
    red_flags=RED_FLAGS,
    schema=SCHEMA,
)
