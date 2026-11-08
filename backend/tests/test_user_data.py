from collections.abc import Iterator
from datetime import date, timedelta

import psycopg
import pytest
from fastapi.testclient import TestClient

from haver import demo
from haver.config import Settings
from haver.core.llm import LLMResponse, ToolCall
from haver.core.plugin import ensure_schemas
from haver.main import create_app
from haver.plugins import PLUGINS
from haver.plugins.insights import MIN_WEEKS, compare, describe, pearson
from haver.plugins.sleep.log import summarise as sleep_summary
from haver.plugins.training.log import summarise as workout_summary
from tests.fakes import ScriptedLLM

TODAY = date.today()


@pytest.fixture
def db(conn: psycopg.Connection) -> Iterator[psycopg.Connection]:
    conn.execute("DROP TABLE IF EXISTS workouts, sleep_logs")
    ensure_schemas(conn, PLUGINS)
    yield conn
    conn.execute("DROP TABLE IF EXISTS workouts, sleep_logs")


def workout(conn: psycopg.Connection, days_ago: int, kind: str, minutes: int) -> None:
    conn.execute(
        "INSERT INTO workouts (day, kind, minutes) VALUES (%s, %s, %s)",
        (TODAY - timedelta(days=days_ago), kind, minutes),
    )


def test_workout_numbers_come_from_the_database(db: psycopg.Connection) -> None:
    workout(db, 1, "strength", 50)
    workout(db, 3, "strength", 40)
    workout(db, 4, "yoga", 30)
    workout(db, 20, "strength", 99)  # outside a 14-day window
    text = workout_summary(db, 14)
    assert "3 session(s) in total" in text
    assert "strength: 2 session(s), 90 minutes" in text
    assert "yoga: 1 session(s), 30 minutes" in text
    assert "strength: 3 session(s)" in workout_summary(db, 30, "strength")
    assert "yoga" not in workout_summary(db, 30, "strength")


def test_the_window_includes_today_and_excludes_the_day_it_starts_after(
    db: psycopg.Connection,
) -> None:
    workout(db, 0, "run", 20)
    workout(db, 7, "run", 20)  # 7 days ago is outside "the last 7 days"
    assert "1 session(s) in total" in workout_summary(db, 7)


def test_no_workouts_is_said_plainly(db: psycopg.Connection) -> None:
    assert workout_summary(db, 14) == "No workouts logged in the last 14 days."


def test_sleep_summary(db: psycopg.Connection) -> None:
    for days_ago, hours in [(0, 8), (1, 5), (2, 7), (30, 3)]:
        db.execute(
            "INSERT INTO sleep_logs (day, hours) VALUES (%s, %s)",
            (TODAY - timedelta(days=days_ago), hours),
        )
    assert sleep_summary(db, 7) == (
        "Sleep in the last 7 days: 3 night(s) logged, average 6.7 hours, 1 night(s) under 6 hours."
    )
    assert sleep_summary(db, 1).startswith("Sleep in the last 1 days: 1 night(s)")


def test_no_sleep_is_said_plainly(db: psycopg.Connection) -> None:
    assert sleep_summary(db, 7) == "No sleep logged in the last 7 days."


def test_pearson_and_its_wording() -> None:
    assert pearson([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)
    assert pearson([1, 2, 3], [6, 4, 2]) == pytest.approx(-1.0)
    assert pearson([1, 1, 1], [1, 2, 3]) is None
    assert describe(0.1) == "weak positive"
    assert describe(-0.45) == "moderate negative"
    assert describe(0.9) == "strong positive"
    assert describe(0.0) == "no clear"


def test_the_link_needs_enough_weeks_and_says_so(db: psycopg.Connection) -> None:
    assert f"At least {MIN_WEEKS}" in compare(db, 12)


def test_the_demo_trainee_shows_the_built_in_link(db: psycopg.Connection) -> None:
    assert demo.seed(db) is True
    text = compare(db, 12)
    assert "Compared 12 weeks" in text
    assert "strong positive" in text
    assert "not proof that one causes the other" in text


def test_seeding_never_overwrites_real_data(db: psycopg.Connection) -> None:
    workout(db, 1, "run", 30)
    assert demo.seed(db) is False
    assert db.execute("SELECT count(*) FROM workouts").fetchone() == (1,)
    assert db.execute("SELECT count(*) FROM sleep_logs").fetchone() == (0,)


def test_seeding_twice_adds_nothing(db: psycopg.Connection) -> None:
    demo.seed(db)
    before = db.execute("SELECT count(*) FROM workouts").fetchone()
    assert demo.seed(db) is False
    assert db.execute("SELECT count(*) FROM workouts").fetchone() == before


def test_an_incomplete_week_of_sleep_is_not_read_as_short_sleep(db: psycopg.Connection) -> None:
    demo.seed(db)
    monday = TODAY - timedelta(days=TODAY.weekday())
    # Leave the oldest week with 4 nights: it must drop out, not count as a low week.
    db.execute(
        "DELETE FROM sleep_logs WHERE day >= %s AND day < %s + 7 AND day > %s + 3",
        (monday - timedelta(weeks=12),) * 2 + (monday - timedelta(weeks=12),),
    )
    assert "Compared 11 weeks" in compare(db, 12)


@pytest.fixture
def client(settings: Settings, db: psycopg.Connection) -> Iterator[TestClient]:
    db.execute("DROP TABLE IF EXISTS documents, memories")
    llm = ScriptedLLM(
        LLMResponse(tool_calls=[ToolCall(id="1", name="workout_summary", arguments={"days": 14})]),
        LLMResponse(
            tool_calls=[
                ToolCall(
                    id="2",
                    name="respond",
                    arguments={"claims": [{"text": "You trained.", "sources": ["log-workouts"]}]},
                )
            ]
        ),
    )
    seeded = settings.model_copy(update={"seed_demo_data": True})
    with TestClient(create_app(seeded, llm=llm)) as test_client:
        yield test_client


def test_the_agent_answers_from_the_log_and_cites_it(client: TestClient) -> None:
    body = client.post("/api/chat", json={"message": "What did I do?"}).json()
    assert [s["tool"] for s in body["steps"]] == ["safety_check", "workout_summary", "respond"]
    assert body["claims"][0]["source_ids"] == ["log-workouts"]
    assert body["citations"][0]["title"] == "Your workout log"


def test_demo_data_is_off_unless_asked(settings: Settings, db: psycopg.Connection) -> None:
    assert settings.seed_demo_data is False
    with TestClient(create_app(settings, llm=ScriptedLLM())) as client:
        client.get("/api/memory")
    assert db.execute("SELECT count(*) FROM workouts").fetchone() == (0,)


def test_the_tool_input_is_validated(db: psycopg.Connection) -> None:
    from haver.core.agent import run_agent

    bad = ToolCall(id="1", name="workout_summary", arguments={"days": 100000})
    respond = ToolCall(id="2", name="respond", arguments={"missing_topic": "x"})
    llm = ScriptedLLM(LLMResponse(tool_calls=[bad]), LLMResponse(tool_calls=[respond]))
    from haver.plugins.training.log import workout_tool

    result = run_agent(llm, [workout_tool(db)], "q")
    assert result.steps[0].ok is False


def test_unlogged_workout_weeks_are_not_read_as_skipped_training(db: psycopg.Connection) -> None:
    demo.seed(db)
    monday = TODAY - timedelta(days=TODAY.weekday())
    db.execute("DELETE FROM workouts WHERE day < %s", (monday - timedelta(weeks=4),))
    assert "Only 4 week(s)" in compare(db, 12)


def test_the_link_has_the_right_sign_and_exact_value(db: psycopg.Connection) -> None:
    monday = TODAY - timedelta(days=TODAY.weekday())
    # Six complete weeks: more sleep goes with more strength minutes, exactly linear.
    for i in range(6):
        week = monday - timedelta(weeks=6 - i)
        for d in range(7):
            db.execute(
                "INSERT INTO sleep_logs (day, hours) VALUES (%s, %s)",
                (week + timedelta(days=d), 5 + i),
            )
        db.execute(
            "INSERT INTO workouts (day, kind, minutes) VALUES (%s, 'strength', %s)",
            (week + timedelta(days=2), 30 + 10 * i),
        )
    text = compare(db, 12)
    assert "r = 1.00" in text and "strong positive" in text
    assert "treat it as a hint" in text  # only 6 weeks


def test_week_boundaries(db: psycopg.Connection) -> None:
    monday = TODAY - timedelta(days=TODAY.weekday())
    last_week = monday - timedelta(weeks=1)
    for d in range(7):  # Monday to Sunday of the last complete week
        db.execute(
            "INSERT INTO sleep_logs (day, hours) VALUES (%s, 8)",
            (last_week + timedelta(days=d),),
        )
    db.execute(
        "INSERT INTO workouts (day, kind, minutes) VALUES (%s, 'strength', 50)", (last_week,)
    )
    # Monday of the current week is outside the window, so it adds no week.
    db.execute("INSERT INTO sleep_logs (day, hours) VALUES (%s, 8)", (monday,))
    assert "Only 1 week(s)" in compare(db, 6)


def _week(db: psycopg.Connection, weeks_ago: int, nights: int, kind: str | None) -> None:
    monday = TODAY - timedelta(days=TODAY.weekday())
    start = monday - timedelta(weeks=weeks_ago)
    for d in range(nights):
        db.execute(
            "INSERT INTO sleep_logs (day, hours) VALUES (%s, %s)",
            (start + timedelta(days=d), 6 + weeks_ago % 3),
        )
    if kind:
        db.execute(
            "INSERT INTO workouts (day, kind, minutes) VALUES (%s, %s, %s)",
            (start, kind, 30 + 5 * weeks_ago),
        )


def test_four_nights_do_not_make_a_week_but_five_do(db: psycopg.Connection) -> None:
    for w in range(1, 7):
        _week(db, w, 5, "strength")
    assert "Compared 6 weeks" in compare(db, 12)
    db.execute(
        "DELETE FROM sleep_logs WHERE day = %s", (TODAY - timedelta(days=TODAY.weekday() + 3),)
    )  # drops a night from last week: 4 left
    assert "Only 5 week(s)" in compare(db, 12)


def test_a_week_with_only_yoga_counts_as_logged_with_zero_strength(
    db: psycopg.Connection,
) -> None:
    for w in range(1, 7):
        _week(db, w, 7, "strength" if w > 1 else "yoga")
    assert "Compared 6 weeks" in compare(db, 12)
