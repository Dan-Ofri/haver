from collections.abc import Iterator

import psycopg
import pytest
from fastapi.testclient import TestClient

from haver.config import Settings
from haver.main import create_app


@pytest.fixture
def client(settings: Settings, conn: psycopg.Connection) -> Iterator[TestClient]:
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def test_a_question_goes_through_every_layer(client: TestClient) -> None:
    response = client.post("/api/chat", json={"message": "How much protein builds muscle?"})
    assert response.status_code == 200
    body = response.json()
    assert [c["id"] for c in body["citations"]] == ["protein-for-muscle-gain"]
    assert body["steps"][0]["tool"] == "search_knowledge"
    assert "[doc:protein-for-muscle-gain]" in body["answer"]


def test_says_it_does_not_know_when_nothing_matches(client: TestClient) -> None:
    body = client.post("/api/chat", json={"message": "keto recipe for dinner"}).json()
    assert body["answer"].startswith("I don't know")
    assert body["citations"] == []


def test_rejects_an_empty_message(client: TestClient) -> None:
    assert client.post("/api/chat", json={"message": ""}).status_code == 422
