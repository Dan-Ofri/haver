import os
from collections.abc import Iterator

import psycopg
import pytest

from haver.config import Settings

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://haver:haver@localhost:5432/haver"
)


@pytest.fixture
def settings() -> Settings:
    # Hermetic: never read a developer's real .env during tests.
    return Settings(_env_file=None, database_url=TEST_DATABASE_URL, llm_provider="offline")


@pytest.fixture
def conn() -> Iterator[psycopg.Connection]:
    """A real database, rolled back to empty after each test. Required in CI."""
    try:
        # Autocommit, so this connection never holds locks that the app's own connections wait on.
        connection = psycopg.connect(TEST_DATABASE_URL, connect_timeout=2, autocommit=True)
    except psycopg.OperationalError:
        if os.environ.get("CI"):
            raise
        pytest.skip("no test database: run `docker compose up -d db`")
    with connection:
        connection.execute("DROP TABLE IF EXISTS documents")
        yield connection
        connection.execute("DROP TABLE IF EXISTS documents")
