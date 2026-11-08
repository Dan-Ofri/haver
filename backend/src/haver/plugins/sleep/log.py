"""The sleep log and the tool that summarises it. Every number is computed by the database."""

import psycopg
from pydantic import BaseModel, Field

from haver.core.tools import Source, Tool, ToolOutput

SCHEMA = """
CREATE TABLE IF NOT EXISTS sleep_logs (
    day date PRIMARY KEY,
    hours numeric(4, 2) NOT NULL CHECK (hours >= 0 AND hours <= 24)
);
"""

LOG_SOURCE = Source(id="log-sleep", title="Your sleep log", url="#your-log")


class SleepArgs(BaseModel):
    days: int = Field(ge=1, le=365, description="How many days back, today included.")


def summarise(conn: psycopg.Connection, days: int) -> str:
    row = conn.execute(
        """
        SELECT count(*), round(avg(hours), 1), count(*) FILTER (WHERE hours < 6)
        FROM sleep_logs WHERE day > current_date - %s AND day <= current_date
        """,
        (days,),
    ).fetchone()
    if row is None or row[0] == 0:
        return f"No sleep logged in the last {days} days."
    return (
        f"Sleep in the last {days} days: {row[0]} night(s) logged, average {row[1]} hours, "
        f"{row[2]} night(s) under 6 hours."
    )


def sleep_tool(conn: psycopg.Connection) -> Tool:
    def run(args: SleepArgs) -> ToolOutput:
        return ToolOutput(content=summarise(conn, args.days), sources=[LOG_SOURCE])

    return Tool(
        name="sleep_summary",
        description=(
            "Average hours, nights logged and short nights over the last N days. "
            "Use it for any question about the user's own sleep."
        ),
        args_model=SleepArgs,
        run=run,
    )
