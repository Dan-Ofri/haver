"""Run the eval set against the configured model and database: uv run python -m haver.evals

A case passes when the answer cites every expected document, or, when none is expected,
answers "not found" and cites nothing. Runs against the configured model: with Gemini it
uses your quota.
"""

import sys
import time
from pathlib import Path

import psycopg
from pydantic import BaseModel, TypeAdapter

from haver.config import get_settings
from haver.core import knowledge, memory
from haver.core.agent import AgentResult, run_agent
from haver.core.embedding import Embedder
from haver.core.llm import LLM
from haver.core.plugin import Plugin, all_tools, knowledge_dirs
from haver.plugins import PLUGINS
from haver.providers import build_embedder, build_llm
from haver.providers.offline_embedder import HashingEmbedder

CASES_FILE = Path(__file__).parents[2] / "evals" / "cases.json"


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


def main() -> int:
    settings = get_settings()
    with psycopg.connect(settings.database_url) as conn:
        outcomes = run(build_llm(settings), conn, load_cases(), build_embedder(settings))
    passes = sum(ok for _, ok in outcomes)
    print(f"\n{passes}/{len(outcomes)} passed ({settings.llm_provider})")
    return 0 if passes == len(outcomes) else 1


if __name__ == "__main__":
    sys.exit(main())
