"""A made-up trainee for demos and tests. It contains no real person's data.

Twelve weeks of sleep and workouts, generated from a fixed seed. One link is built in on purpose:
in weeks of short sleep the trainee skips strength sessions, so the agent has something to find.
"""

import random
from datetime import date, timedelta

import psycopg

WEEKS = 12


def seed(conn: psycopg.Connection, today: date | None = None) -> bool:
    """Fill empty logs. Returns False, and changes nothing, if either log already has rows."""
    # One seeder at a time across processes; the lock is released when the transaction ends.
    conn.execute("SELECT pg_advisory_xact_lock(7461)")
    if today is None:
        row = conn.execute("SELECT current_date").fetchone()  # the same clock the tools use
        today = row[0] if row else date.today()
    for table in ("workouts", "sleep_logs"):
        if conn.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone():  # noqa: S608
            return False
    rng = random.Random(7)  # noqa: S311 (made-up data, not security)
    monday = today - timedelta(days=today.weekday())
    first = monday - timedelta(weeks=WEEKS)
    for week in range(WEEKS):
        start = first + timedelta(weeks=week)
        short_week = week % 3 == 2
        base = 5.6 if short_week else 7.4
        for offset in range(7):
            day = start + timedelta(days=offset)
            if day > today:
                continue
            hours = round(max(3.5, min(9.5, rng.gauss(base, 0.5))), 2)
            conn.execute("INSERT INTO sleep_logs (day, hours) VALUES (%s, %s)", (day, hours))
        plan = [(0, "strength", 55), (2, "strength", 55), (4, "yoga", 40), (5, "run", 45)]
        if not short_week:
            plan.append((3, "strength", 60))
        for offset, kind, minutes in plan:
            day = start + timedelta(days=offset)
            if day <= today:
                conn.execute(
                    "INSERT INTO workouts (day, kind, minutes) VALUES (%s, %s, %s)",
                    (day, kind, minutes),
                )
    return True
