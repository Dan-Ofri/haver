import psycopg

from haver.core.agent import NOT_FOUND, STEP_LIMIT, AgentResult, NotFound
from haver.core.llm import LLMResponse, Message, ToolSpec
from haver.evals import Case, load_cases, load_safety_cases, main, passed, run, run_safety
from haver.providers.offline import OfflineLLM
from haver.providers.offline_embedder import HashingEmbedder
from tests.fakes import ScriptedLLM


def test_eval_set_runs_end_to_end_with_the_offline_model(conn: psycopg.Connection) -> None:
    outcomes = run(OfflineLLM(), conn, load_cases(), HashingEmbedder())
    assert len(outcomes) == 5  # the semantic-only case is skipped offline
    assert all(ok for _, ok in outcomes)


def test_running_out_of_steps_is_not_a_correct_not_found() -> None:
    case = Case(question="q", expected_citations=[])
    stalled = NotFound(message=STEP_LIMIT, out_of_steps=True)
    assert passed(case, AgentResult(not_found=NotFound(message=NOT_FOUND)))
    assert not passed(case, AgentResult(not_found=stalled))


def test_the_safety_eval_wants_the_right_flag_and_lets_safe_questions_through() -> None:
    cases = load_safety_cases()
    assert cases.model_only, "the model layer needs cases the patterns miss"
    results = run_safety(ScriptedLLM(triage="none"), cases)
    total = len(cases.red_flags) + len(cases.model_only) + len(cases.safe)
    assert len(results) == total
    assert sum(ok for _, ok in results) == len(cases.safe)


def test_the_safety_eval_passes_a_model_that_names_every_flag_right() -> None:
    cases = load_safety_cases()
    want = {c.question: c.flag for c in cases.red_flags + cases.model_only}

    class Perfect:
        def complete(
            self, system: str, messages: list[Message], tools: list[ToolSpec]
        ) -> LLMResponse:
            question = messages[-1].content.split("\n")[1]
            return LLMResponse(text=want.get(question, "none"))

    plain = [q for q in want if "<" not in q and ">" not in q]
    assert len(plain) == len(want)  # the fake reads the question back unescaped
    assert all(ok for _, ok in run_safety(Perfect(), cases))


def test_unknown_eval_arguments_are_rejected() -> None:
    assert main(["--saftey"]) == 2
