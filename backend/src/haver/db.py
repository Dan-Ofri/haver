"""Database access helpers."""

import psycopg


def ping(database_url: str, timeout_seconds: int = 2) -> bool:
    """Return True when the database answers a trivial query."""
    try:
        with psycopg.connect(database_url, connect_timeout=timeout_seconds) as conn:
            conn.execute("SELECT 1")
        return True
    except psycopg.Error:
        return False
