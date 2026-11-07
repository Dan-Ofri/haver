import os
from collections.abc import Iterator

import psycopg
import pytest

from haver.config import Settings

# Tests use their own database, so they never wipe the one the running app uses.
ADMIN_DATABASE_URL = os.environ.get(
    "TEST_ADMIN_DATABASE_URL", "postgresql://haver:haver@localhost:5432/haver"
)
TEST_DATABASE_URL = ADMIN_DATABASE_URL.rsplit("/", 1)[0] + "/haver_test"


@pytest.fixture(scope="session")
def test_database() -> str:
    """Create the test database once. Required in CI, skipped locally when Postgres is down."""
    try:
        admin = psycopg.connect(ADMIN_DATABASE_URL, connect_timeout=2, autocommit=True)
    except psycopg.OperationalError:
        if os.environ.get("CI"):
            raise
        pytest.skip("no database: run `docker compose up -d db`")
    with admin:
        exists = admin.execute("SELECT 1 FROM pg_database WHERE datname = 'haver_test'").fetchone()
        if not exists:
            admin.execute("CREATE DATABASE haver_test")
    return TEST_DATABASE_URL


@pytest.fixture
def settings() -> Settings:
    # Hermetic: never read a developer's real .env during tests.
    return Settings(_env_file=None, database_url=TEST_DATABASE_URL, llm_provider="offline")


@pytest.fixture
def conn(test_database: str) -> Iterator[psycopg.Connection]:
    """A real database, emptied before and after each test."""
    # Autocommit, so this connection never holds locks that the app's own connections wait on.
    with psycopg.connect(test_database, autocommit=True) as connection:
        connection.execute("DROP TABLE IF EXISTS documents, memories")
        yield connection
        connection.execute("DROP TABLE IF EXISTS documents, memories")
