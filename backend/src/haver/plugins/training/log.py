"""The workout log and the tool that summarises it. Every number is computed by the database."""

from typing import Literal

import psycopg
from pydantic import BaseModel, Field

from haver.core.tools import Source, Tool, ToolOutput

SCHEMA = """
CREATE TABLE IF NOT EXISTS workouts (
    id serial PRIMARY KEY,
    day date NOT NULL,
    kind text NOT NULL CHECK (kind IN ('strength', 'run', 'swim', 'yoga')),
    minutes integer NOT NULL CHECK (minutes > 0)
);
CREATE INDEX IF NOT EXISTS workouts_day_idx ON workouts (day);
"""

LOG_SOURCE = Source(id="log-workouts", title="Your workout log", url="#your-log")

Kind = Literal["strength", "run", "swim", "yoga"]


class WorkoutArgs(BaseModel):
    days: int = Field(ge=1, le=365, description="How many days back, today included.")
    kind: Kind | None = Field(default=None, description="Only this kind of workout.")


def summarise(conn: psycopg.Connection, days: int, kind: str | None = None) -> str:
    rows = conn.execute(
        """
        SELECT kind, count(*), sum(minutes) FROM workouts
        WHERE day > current_date - %s AND day <= current_date AND (%s::text IS NULL OR kind = %s)
        GROUP BY kind ORDER BY kind
        """,
        (days, kind, kind),
    ).fetchall()
    window = f"the last {days} days"
    if not rows:
        return f"No workouts logged in {window}."
    total = sum(r[1] for r in rows)
    lines = [f"- {r[0]}: {r[1]} session(s), {r[2]} minutes" for r in rows]
    return f"Workouts in {window}: {total} session(s) in total.\n" + "\n".join(lines)


def workout_tool(conn: psycopg.Connection) -> Tool:
    def run(args: WorkoutArgs) -> ToolOutput:
        return ToolOutput(content=summarise(conn, args.days, args.kind), sources=[LOG_SOURCE])

    return Tool(
        name="workout_summary",
        description=(
            "Count the user's logged workouts and total minutes over the last N days, "
            "optionally for one kind. Use it for any question about what the user did."
        ),
        args_model=WorkoutArgs,
        run=run,
    )
