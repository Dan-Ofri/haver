import psycopg

from haver.evals import load_cases, run
from haver.providers.offline import OfflineLLM


def test_eval_set_runs_end_to_end_with_the_offline_model(conn: psycopg.Connection) -> None:
    outcomes = run(OfflineLLM(), conn, load_cases())
    assert len(outcomes) == 5
    assert all(ok for _, ok in outcomes)
