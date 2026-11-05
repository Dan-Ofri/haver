from typing import Any

from pydantic import BaseModel

from haver.core.agent import (
    NOT_FOUND,
    NUDGE,
    RESPOND_ALONE,
    RESPOND_ONCE,
    RESPOND_SPEC,
    STEP_LIMIT,
    run_agent,
)
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
    assert [(s.tool, s.ok) for s in result.steps] == [("lookup", True), ("respond", True)]
    assert llm.calls[1][-1].content == "facts about sleep"


def test_respond_is_offered_to_the_model() -> None:
    llm = ScriptedLLM(respond(missing_topic="x"))
    run_agent(llm, [lookup_tool()], "q")
    assert [t.name for t in llm.tools[0]] == ["lookup", "respond"]
    assert llm.tools[0][1] == RESPOND_SPEC
    assert "$ref" not in str(RESPOND_SPEC.parameters)


def test_an_answer_sent_with_a_search_is_refused_whatever_the_order() -> None:
    for answer_first in (True, False):
        invented = {"claims": [claim("Take 10 mg melatonin.", "sleep")]}
        calls = [
            ToolCall(id="1", name="lookup", arguments={"topic": "sleep"}),
            ToolCall(id="2", name="respond", arguments=invented),
        ]
        if answer_first:
            calls.reverse()
        llm = ScriptedLLM(LLMResponse(tool_calls=calls), respond(claims=[claim("Sleep.", "sleep")]))
        result = run_agent(llm, [lookup_tool()], "q")
        assert [c.text for c in result.claims] == ["Sleep."]
        replies = [(m.tool_name, m.content) for m in llm.calls[1] if m.role == "tool"]
        expected = [("lookup", "facts about sleep"), ("respond", RESPOND_ALONE)]
        assert replies == (expected[::-1] if answer_first else expected)


def test_free_text_fields_cannot_carry_advice() -> None:
    long_question = "Adults need 1.6 g/kg of protein a day, " * 4 + "right?"
    for answer in (
        respond(missing_topic="   "),
        respond(missing_topic="x" * 61),
        respond(missing_topic="keto", ask_instead=["Eat 1.6 g/kg of protein."]),
        respond(missing_topic="keto", ask_instead=[long_question]),
    ):
        result = run_agent(ScriptedLLM(answer, respond(missing_topic="keto")), [lookup_tool()], "q")
        assert result.steps[0].detail == "invalid answer"


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
    answer = respond(missing_topic="keto recipes", ask_instead=["How much protein?"])
    result = run_agent(ScriptedLLM(call(topic="sleep"), answer), [lookup_tool()], "keto?")
    assert result.not_found is not None
    assert result.not_found.message == "I couldn't find a reliable source on keto recipes."
    assert result.not_found.ask_instead == ["How much protein?"]
    assert [s.id for s in result.not_found.related] == ["sleep", "naps"]
    assert result.citations == []


def test_the_loop_allows_searching_again_before_answering() -> None:
    # Whether a real model retries is up to the prompt, and is measured by the eval set.
    llm = ScriptedLLM(
        call(topic="nothing"),
        call(topic="sleep"),
        respond(claims=[claim("Sleep 7 hours.", "sleep")]),
    )
    result = run_agent(llm, [lookup_tool()], "q")
    assert [s.detail for s in result.steps] == ["0 result(s)", "2 result(s)", "1 claim(s)"]
    assert [c.text for c in result.claims] == ["Sleep 7 hours."]


def test_an_invalid_answer_goes_back_to_the_model() -> None:
    llm = ScriptedLLM(respond(claims=[]), respond(missing_topic="rowing"))
    result = run_agent(llm, [lookup_tool()], "q")
    assert result.steps[0].ok is False
    assert llm.calls[1][-1].content.startswith("Error:")
    assert result.not_found is not None and result.not_found.topic == "rowing"


def test_plain_text_is_nudged_once_then_becomes_not_found() -> None:
    llm = ScriptedLLM(LLMResponse(text="Eat 5 g/kg."), LLMResponse(text="Really, 5 g/kg."))
    result = run_agent(llm, [lookup_tool()], "q")
    assert llm.calls[1][-1].content == NUDGE
    assert result.claims == []
    assert result.not_found is not None and result.not_found.message == NOT_FOUND


def test_rejects_invalid_tool_arguments_and_lets_the_model_retry() -> None:
    llm = ScriptedLLM(call(wrong="x"), call(topic="sleep"), respond(claims=[claim("ok", "sleep")]))
    result = run_agent(llm, [lookup_tool()], "q")
    assert [(s.tool, s.ok) for s in result.steps][:2] == [("lookup", False), ("lookup", True)]
    assert llm.calls[1][-1].content.startswith("Error:")


def test_reports_an_unknown_tool_to_the_model() -> None:
    llm = ScriptedLLM(call("delete_everything"), respond(missing_topic="x"))
    result = run_agent(llm, [lookup_tool()], "q")
    assert result.steps[0].ok is False
    assert llm.calls[1][-1].content == "Error: unknown tool 'delete_everything'."


def test_stops_at_the_step_limit() -> None:
    llm = ScriptedLLM(*[call(topic="x") for _ in range(3)])
    result = run_agent(llm, [lookup_tool()], "q", max_steps=3)
    assert result.claims == []
    assert result.not_found is not None and result.not_found.message == STEP_LIMIT
    assert result.not_found.out_of_steps
    assert len(result.steps) == 3


def test_adds_up_token_usage_and_time() -> None:
    first = call(topic="x")
    first.input_tokens, first.output_tokens = 10, 2
    last = respond(missing_topic="x")
    last.input_tokens, last.output_tokens = 20, 5
    result = run_agent(ScriptedLLM(first, last), [lookup_tool()], "q")
    assert (result.input_tokens, result.output_tokens) == (30, 7)
    assert result.duration_ms >= 0


def test_a_nudge_followed_by_a_valid_answer_works() -> None:
    llm = ScriptedLLM(
        LLMResponse(text="hmm"), call(topic="sleep"), respond(claims=[claim("Sleep.", "sleep")])
    )
    result = run_agent(llm, [lookup_tool()], "q")
    assert [c.text for c in result.claims] == ["Sleep."]


def test_an_invalid_answer_on_the_last_step_ends_with_the_step_limit() -> None:
    llm = ScriptedLLM(call(topic="sleep"), respond(claims=[]))
    result = run_agent(llm, [lookup_tool()], "q", max_steps=2)
    assert result.not_found is not None and result.not_found.message == STEP_LIMIT


def test_every_answer_in_a_turn_gets_its_own_response() -> None:
    two = LLMResponse(
        tool_calls=[
            ToolCall(id="a", name="respond", arguments={"missing_topic": "x"}),
            ToolCall(id="b", name="respond", arguments={"missing_topic": "y"}),
        ]
    )
    llm = ScriptedLLM(two, respond(missing_topic="z"))
    result = run_agent(llm, [lookup_tool()], "q")
    replies = [m for m in llm.calls[1] if m.role == "tool"]
    assert [(m.tool_call_id, m.content) for m in replies] == [
        ("a", RESPOND_ONCE),
        ("b", RESPOND_ONCE),
    ]
    assert result.not_found is not None and result.not_found.topic == "z"


def test_all_claims_dropped_without_a_topic_gives_the_generic_not_found() -> None:
    answer = respond(claims=[claim("Invented.", "made-up")], ask_instead=["How long to sleep?"])
    result = run_agent(ScriptedLLM(call(topic="sleep"), answer), [lookup_tool()], "q")
    assert result.not_found is not None
    assert result.not_found.message == NOT_FOUND
    assert result.not_found.ask_instead == ["How long to sleep?"]
