from typing import Any

from pydantic import BaseModel

from haver.core.agent import NOT_FOUND, NUDGE, RESPOND_SPEC, run_agent
from haver.core.llm import LLMResponse, ToolCall
from haver.core.tools import Source, Tool, ToolOutput
from tests.fakes import ScriptedLLM


class LookupArgs(BaseModel):
    topic: str


def lookup_tool() -> Tool:
    def run(args: LookupArgs) -> ToolOutput:
        if args.topic == "nothing":
            return ToolOutput(content="No documents found.")
        return ToolOutput(
            content=f"facts about {args.topic}",
            sources=[
                Source(id="sleep", title="Sleep", url="https://example.org/sleep"),
                Source(id="naps", title="Naps", url="https://example.org/naps"),
            ],
        )

    return Tool(name="lookup", description="Look up a topic.", args_model=LookupArgs, run=run)


def call(name: str = "lookup", **arguments: Any) -> LLMResponse:
    return LLMResponse(tool_calls=[ToolCall(id="1", name=name, arguments=arguments)])


def respond(**arguments: Any) -> LLMResponse:
    return call("respond", **arguments)


def claim(text: str, *sources: str) -> dict[str, Any]:
    return {"text": text, "sources": list(sources)}


def test_answers_with_claims_and_their_sources() -> None:
    llm = ScriptedLLM(call(topic="sleep"), respond(claims=[claim("Sleep 7 hours.", "sleep")]))
    result = run_agent(llm, [lookup_tool()], "How long should I sleep?")
    assert [(c.text, c.source_ids) for c in result.claims] == [("Sleep 7 hours.", ["sleep"])]
    assert [s.id for s in result.citations] == ["sleep"]
    assert result.not_found is None
    assert [(s.tool, s.ok) for s in result.steps] == [("lookup", True)]
    assert llm.calls[1][-1].content == "facts about sleep"


def test_respond_is_offered_to_the_model() -> None:
    llm = ScriptedLLM(respond(missing="x"))
    run_agent(llm, [lookup_tool()], "q")
    assert RESPOND_SPEC.parameters["properties"]["claims"]["items"]["properties"]["sources"]


def test_drops_each_claim_with_a_source_never_retrieved() -> None:
    answer = respond(claims=[claim("Sleep 7 hours.", "sleep"), claim("Take melatonin.", "made-up")])
    result = run_agent(ScriptedLLM(call(topic="sleep"), answer), [lookup_tool()], "q")
    assert [c.text for c in result.claims] == ["Sleep 7 hours."]
    assert result.dropped_citations == ["made-up"]


def test_a_claim_mixing_real_and_invented_sources_is_dropped() -> None:
    answer = respond(claims=[claim("Nap daily.", "naps", "made-up")])
    result = run_agent(ScriptedLLM(call(topic="sleep"), answer), [lookup_tool()], "q")
    assert result.claims == []
    assert result.not_found is not None


def test_not_found_is_helpful() -> None:
    answer = respond(missing="Nothing on keto recipes.", ask_instead=["How much protein?"])
    result = run_agent(ScriptedLLM(call(topic="sleep"), answer), [lookup_tool()], "keto?")
    assert result.not_found is not None
    assert result.not_found.missing == "Nothing on keto recipes."
    assert result.not_found.ask_instead == ["How much protein?"]
    assert [s.id for s in result.not_found.related] == ["sleep", "naps"]
    assert result.citations == []


def test_retries_the_search_before_giving_up() -> None:
    llm = ScriptedLLM(
        call(topic="nothing"),
        call(topic="sleep"),
        respond(claims=[claim("Sleep 7 hours.", "sleep")]),
    )
    result = run_agent(llm, [lookup_tool()], "q")
    assert [s.detail for s in result.steps] == ["0 result(s)", "2 result(s)"]
    assert [c.text for c in result.claims] == ["Sleep 7 hours."]


def test_an_invalid_answer_goes_back_to_the_model() -> None:
    llm = ScriptedLLM(respond(claims=[]), respond(missing="Not covered."))
    result = run_agent(llm, [lookup_tool()], "q")
    assert result.steps[0].ok is False
    assert llm.calls[1][-1].content.startswith("Error:")
    assert result.not_found is not None and result.not_found.missing == "Not covered."


def test_plain_text_is_nudged_once_then_becomes_not_found() -> None:
    llm = ScriptedLLM(LLMResponse(text="Eat 5 g/kg."), LLMResponse(text="Really, 5 g/kg."))
    result = run_agent(llm, [lookup_tool()], "q")
    assert llm.calls[1][-1].content == NUDGE
    assert result.claims == []
    assert result.not_found is not None and result.not_found.missing == NOT_FOUND


def test_rejects_invalid_tool_arguments_and_lets_the_model_retry() -> None:
    llm = ScriptedLLM(call(wrong="x"), call(topic="sleep"), respond(claims=[claim("ok", "sleep")]))
    result = run_agent(llm, [lookup_tool()], "q")
    assert [(s.tool, s.ok) for s in result.steps] == [("lookup", False), ("lookup", True)]
    assert llm.calls[1][-1].content.startswith("Error:")


def test_reports_an_unknown_tool_to_the_model() -> None:
    llm = ScriptedLLM(call("delete_everything"), respond(missing="x"))
    result = run_agent(llm, [lookup_tool()], "q")
    assert result.steps[0].ok is False
    assert llm.calls[1][-1].content == "Error: unknown tool 'delete_everything'."


def test_stops_at_the_step_limit() -> None:
    llm = ScriptedLLM(*[call(topic="x") for _ in range(3)])
    result = run_agent(llm, [lookup_tool()], "q", max_steps=3)
    assert result.claims == []
    assert result.not_found is not None and result.not_found.missing == NOT_FOUND
    assert len(result.steps) == 3


def test_adds_up_token_usage_and_time() -> None:
    first = call(topic="x")
    first.input_tokens, first.output_tokens = 10, 2
    last = respond(missing="x")
    last.input_tokens, last.output_tokens = 20, 5
    result = run_agent(ScriptedLLM(first, last), [lookup_tool()], "q")
    assert (result.input_tokens, result.output_tokens) == (30, 7)
    assert result.duration_ms >= 0
