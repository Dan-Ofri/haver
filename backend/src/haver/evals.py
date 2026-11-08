"""Run the eval set against the configured model and database: uv run python -m haver.evals

A case passes when the answer cites every expected document, or, when none is expected,
answers "not found" and cites nothing. Runs against the configured model: with Gemini it
uses your quota.

`uv run python -m haver.evals --safety` checks the model-based safety layer alone, without the
patterns: every red flag must be named correctly and every safe question let through. It needs
no database.
"""

import sys
import time
from pathlib import Path

import psycopg
from pydantic import BaseModel, TypeAdapter

from haver.config import get_settings
from haver.core import knowledge, memory, safety
from haver.core.agent import AgentResult, run_agent
from haver.core.embedding import Embedder
from haver.core.llm import LLM
from haver.core.plugin import Plugin, all_red_flags, all_tools, ensure_schemas, knowledge_dirs
from haver.plugins import PLUGINS
from haver.providers import build_embedder, build_llm
from haver.providers.offline_embedder import HashingEmbedder

CASES_FILE = Path(__file__).parents[2] / "evals" / "cases.json"
RED_FLAGS_FILE = Path(__file__).parents[2] / "evals" / "red_flags.json"


class Case(BaseModel):
    question: str
    expected_citations: list[str]
    # Only meaning-based search can answer it, so a keyword-only embedder skips it.
    needs_semantic_search: bool = False


def load_cases(path: Path = CASES_FILE) -> list[Case]:
    return TypeAdapter(list[Case]).validate_json(path.read_text(encoding="utf-8"))


def passed(case: Case, result: AgentResult) -> bool:
    cited = {source.id for source in result.citations}
    if not case.expected_citations:
        # Running out of steps is a failure, not a correct "not found".
        nf = result.not_found
        return not cited and nf is not None and not nf.out_of_steps
    return set(case.expected_citations) <= cited


def run(
    llm: LLM,
    conn: psycopg.Connection,
    cases: list[Case],
    embedder: Embedder,
    plugins: list[Plugin] = PLUGINS,
) -> list[tuple[Case, bool]]:
    memory.ensure_schema(conn)
    ensure_schemas(conn, plugins)
    knowledge.load(conn, knowledge_dirs(plugins), embedder)
    tools = all_tools(conn, plugins, embedder)
    outcomes = []
    for case in cases:
        if case.needs_semantic_search and isinstance(embedder, HashingEmbedder):
            print(f"SKIP  {case.question}")
            continue
        start = time.perf_counter()
        result = run_agent(llm, tools, case.question)
        ok = passed(case, result)
        outcomes.append((case, ok))
        seconds = time.perf_counter() - start
        tokens = result.input_tokens + result.output_tokens
        print(f"{'PASS' if ok else 'FAIL'}  {seconds:5.1f}s  {tokens:6d} tokens  {case.question}")
    return outcomes


class FlagCase(BaseModel):
    question: str
    flag: str


class SafetyCases(BaseModel):
    red_flags: list[FlagCase]
    # Worded so the patterns miss them: only the model-based layer can catch these.
    model_only: list[FlagCase]
    safe: list[str]


def load_safety_cases(path: Path = RED_FLAGS_FILE) -> SafetyCases:
    return SafetyCases.model_validate_json(path.read_text(encoding="utf-8"))


def run_safety(
    llm: LLM, cases: SafetyCases, plugins: list[Plugin] = PLUGINS
) -> list[tuple[str, bool]]:
    flags = all_red_flags(plugins)
    expected: list[tuple[str, str | None]] = [
        (c.question, c.flag) for c in cases.red_flags + cases.model_only
    ]
    expected += [(q, None) for q in cases.safe]
    outcomes = []
    for question, flag in expected:
        screening = safety.triage(llm, question, flags)
        got = screening.alert.flag_id if screening.alert else None
        ok = got == flag
        outcomes.append((question, ok))
        verdict = "PASS" if ok else "FAIL"
        print(f"{verdict}  want {flag or 'none':9}  got {got or 'none':9}  {question}")
    return outcomes


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv not in ([], ["--safety"]):
        print("usage: python -m haver.evals [--safety]", file=sys.stderr)
        return 2
    settings = get_settings()
    if argv:
        results = run_safety(build_llm(settings), load_safety_cases())
        passes = sum(ok for _, ok in results)
        print(f"\n{passes}/{len(results)} passed ({settings.llm_provider})")
        return 0 if passes == len(results) else 1
    with psycopg.connect(settings.database_url) as conn:
        outcomes = run(build_llm(settings), conn, load_cases(), build_embedder(settings))
    passes = sum(ok for _, ok in outcomes)
    print(f"\n{passes}/{len(outcomes)} passed ({settings.llm_provider})")
    return 0 if passes == len(outcomes) else 1


if __name__ == "__main__":
    sys.exit(main())
