from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from haver import db
from haver.config import Settings
from haver.main import create_app


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def test_health_reports_database_ok(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db, "ping", lambda _url: True)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_stays_up_when_database_is_down(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(db, "ping", lambda _url: False)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["database"] == "unavailable"
