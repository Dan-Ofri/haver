import json
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest
from fastapi.testclient import TestClient

from haver.config import Settings
from haver.core.llm import LLMResponse
from haver.core.safety import check
from haver.main import create_app
from haver.plugins.training.red_flags import RED_FLAGS
from tests.fakes import ScriptedLLM

CASES = json.loads((Path(__file__).parents[1] / "evals" / "red_flags.json").read_text("utf-8"))


@pytest.mark.parametrize("case", CASES["red_flags"], ids=lambda c: c["question"][:40])
def test_every_red_flag_question_is_caught(case: dict[str, str]) -> None:
    alert = check(case["question"], RED_FLAGS)
    assert alert is not None, "red flag missed"
    assert alert.flag_id == case["flag"]


@pytest.mark.parametrize("question", CASES["safe"])
def test_ordinary_training_questions_are_not_blocked(question: str) -> None:
    assert check(question, RED_FLAGS) is None


def test_the_answer_language_follows_the_question() -> None:
    english = check("I feel chest pain when I run", RED_FLAGS)
    hebrew = check("יש לי כאב בחזה כשאני רץ", RED_FLAGS)
    assert english is not None and hebrew is not None
    assert english.message.startswith("Please stop")
    assert hebrew.message.startswith("בבקשה")


def test_a_crisis_message_does_not_tell_the_user_to_train() -> None:
    alert = check("I want to hurt myself", RED_FLAGS)
    assert alert is not None
    assert "exercise" not in alert.message.lower()


@pytest.fixture
def client_and_llm(
    settings: Settings, conn: psycopg.Connection
) -> Iterator[tuple[TestClient, ScriptedLLM]]:
    llm = ScriptedLLM(LLMResponse())
    with TestClient(create_app(settings, llm=llm)) as client:
        yield client, llm


def test_a_red_flag_never_reaches_the_model(
    client_and_llm: tuple[TestClient, ScriptedLLM],
) -> None:
    client, llm = client_and_llm
    body = client.post("/api/chat", json={"message": "My back hurts and my leg is numb."}).json()
    assert body["safety"]["flag_id"] == "nerve"
    assert body["claims"] == [] and body["citations"] == [] and body["steps"] == []
    assert llm.calls == []
