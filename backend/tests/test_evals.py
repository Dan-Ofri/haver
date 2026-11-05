import psycopg

from haver.core.agent import NOT_FOUND, STEP_LIMIT, AgentResult, NotFound
from haver.evals import Case, load_cases, passed, run
from haver.providers.offline import OfflineLLM


def test_eval_set_runs_end_to_end_with_the_offline_model(conn: psycopg.Connection) -> None:
    outcomes = run(OfflineLLM(), conn, load_cases())
    assert len(outcomes) == 5
    assert all(ok for _, ok in outcomes)


def test_running_out_of_steps_is_not_a_correct_not_found() -> None:
    case = Case(question="q", expected_citations=[])
    stalled = NotFound(message=STEP_LIMIT, out_of_steps=True)
    assert passed(case, AgentResult(not_found=NotFound(message=NOT_FOUND)))
    assert not passed(case, AgentResult(not_found=stalled))
