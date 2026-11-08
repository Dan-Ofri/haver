"""Questions that span domains. This plugin may read the tables of several domains; the domains
themselves never read each other's."""

import math

import psycopg
from pydantic import BaseModel, Field

from haver.core.plugin import Plugin
from haver.core.tools import Source, Tool, ToolOutput

MIN_WEEKS = 6
SOURCE = Source(id="log-sleep-training", title="Your sleep and workout logs", url="#your-log")


class LinkArgs(BaseModel):
    weeks: int = Field(default=12, ge=MIN_WEEKS, le=52, description="How many weeks to compare.")


def pearson(xs: list[float], ys: list[float]) -> float | None:
    """The correlation of two equal-length series, or None when one of them does not vary."""
    n = len(xs)
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True))
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x == 0 or var_y == 0:
        return None
    return cov / math.sqrt(var_x * var_y)


def describe(r: float) -> str:
    size = abs(r)
    strength = "weak" if size < 0.3 else "moderate" if size < 0.6 else "strong"
    return f"{strength} {'positive' if r > 0 else 'negative'}"


def compare(conn: psycopg.Connection, weeks: int) -> str:
    """Weekly average sleep against weekly strength minutes, over complete weeks only."""
    rows = conn.execute(
        """
        WITH w AS (
            SELECT generate_series(
                date_trunc('week', current_date)::date - 7 * %(n)s,
                date_trunc('week', current_date)::date - 7, interval '7 days')::date AS week
        )
        SELECT w.week,
               (SELECT avg(hours) FROM sleep_logs s WHERE s.day >= w.week AND s.day < w.week + 7),
               (SELECT count(*) FROM sleep_logs s WHERE s.day >= w.week AND s.day < w.week + 7),
               (SELECT coalesce(sum(minutes), 0) FROM workouts t
                WHERE t.kind = 'strength' AND t.day >= w.week AND t.day < w.week + 7)
        FROM w ORDER BY w.week
        """,
        {"n": weeks},
    ).fetchall()
    # A week counts only with at least 5 logged nights, so a gap is not read as short sleep.
    usable = [(float(r[1]), float(r[3])) for r in rows if r[2] >= 5]
    if len(usable) < MIN_WEEKS:
        return (
            f"Only {len(usable)} complete week(s) of sleep and workout data in the last {weeks} "
            f"weeks. At least {MIN_WEEKS} are needed to compare them, so I can't say."
        )
    r = pearson([u[0] for u in usable], [u[1] for u in usable])
    if r is None:
        return (
            f"Compared {len(usable)} weeks, but sleep or strength minutes did not vary, "
            "so there is nothing to compare."
        )
    return (
        f"Compared {len(usable)} complete weeks of average nightly sleep with strength minutes "
        f"per week. Correlation r = {r:.2f}, a {describe(r)} link. This is an association in "
        "the user's own data, not proof that one causes the other."
    )


def link_tool(conn: psycopg.Connection) -> Tool:
    def run(args: LinkArgs) -> ToolOutput:
        return ToolOutput(content=compare(conn, args.weeks), sources=[SOURCE])

    return Tool(
        name="sleep_training_link",
        description=(
            "Compare weekly average sleep with weekly strength-training minutes over complete "
            "weeks. Use it for questions about how sleep and training relate."
        ),
        args_model=LinkArgs,
        run=run,
    )


def _tools(conn: psycopg.Connection) -> list[Tool]:
    return [link_tool(conn)]


PLUGIN = Plugin(name="insights", tools=_tools)
