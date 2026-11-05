from pydantic import BaseModel

from haver.core.agent import DONT_KNOW, run_agent
from haver.core.llm import LLMResponse, ToolCall
from haver.core.tools import Source, Tool, ToolOutput
from tests.fakes import ScriptedLLM


class LookupArgs(BaseModel):
    topic: str


def lookup_tool() -> Tool:
    def run(args: LookupArgs) -> ToolOutput:
        return ToolOutput(
            content=f"facts about {args.topic}",
            sources=[Source(id="sleep", title="Sleep", url="https://example.org/sleep")],
        )

    return Tool(name="lookup", description="Look up a topic.", args_model=LookupArgs, run=run)


def call(name: str = "lookup", **arguments: object) -> LLMResponse:
    return LLMResponse(tool_calls=[ToolCall(id="1", name=name, arguments=arguments)])


def test_answers_with_a_citation_of_a_retrieved_document() -> None:
    llm = ScriptedLLM(call(topic="sleep"), LLMResponse(text="Sleep 7 hours [doc:sleep]."))
    result = run_agent(llm, [lookup_tool()], "How long should I sleep?")
    assert result.answer == "Sleep 7 hours [doc:sleep]."
    assert [c.id for c in result.citations] == ["sleep"]
    assert result.dropped_citations == []
    assert [(s.tool, s.ok) for s in result.steps] == [("lookup", True)]
    assert llm.calls[1][-1].content == "facts about sleep"


def test_rejects_invalid_arguments_and_lets_the_model_retry() -> None:
    llm = ScriptedLLM(call(wrong="x"), call(topic="sleep"), LLMResponse(text="ok [doc:sleep]"))
    result = run_agent(llm, [lookup_tool()], "q")
    assert [(s.tool, s.ok) for s in result.steps] == [("lookup", False), ("lookup", True)]
    assert llm.calls[1][-1].content.startswith("Error:")
    assert [c.id for c in result.citations] == ["sleep"]


def test_reports_an_unknown_tool_to_the_model() -> None:
    llm = ScriptedLLM(call("delete_everything"), LLMResponse(text="I don't know."))
    result = run_agent(llm, [lookup_tool()], "q")
    assert result.steps[0].ok is False
    assert llm.calls[1][-1].content == "Error: unknown tool 'delete_everything'."


def test_stops_at_the_step_limit() -> None:
    llm = ScriptedLLM(*[call(topic="x") for _ in range(3)])
    result = run_agent(llm, [lookup_tool()], "q", max_steps=3)
    assert "step limit" in result.answer
    assert result.citations == []
    assert len(result.steps) == 3


def test_adds_up_token_usage() -> None:
    first = call(topic="x")
    first.input_tokens, first.output_tokens = 10, 2
    llm = ScriptedLLM(first, LLMResponse(text="I don't know", input_tokens=20, output_tokens=5))
    result = run_agent(llm, [lookup_tool()], "q")
    assert (result.input_tokens, result.output_tokens) == (30, 7)
    assert result.duration_ms >= 0


def test_an_invented_citation_turns_the_answer_into_i_dont_know() -> None:
    llm = ScriptedLLM(call(topic="sleep"), LLMResponse(text="Eat 5 g/kg a day [doc:made-up]."))
    result = run_agent(llm, [lookup_tool()], "q")
    assert result.answer == DONT_KNOW
    assert result.citations == []
    assert result.dropped_citations == ["made-up"]


def test_an_answer_without_any_citation_turns_into_i_dont_know() -> None:
    llm = ScriptedLLM(call(topic="sleep"), LLMResponse(text="Sleep 9 hours."))
    result = run_agent(llm, [lookup_tool()], "q")
    assert result.answer == DONT_KNOW


def test_keeps_the_models_own_i_dont_know_with_any_apostrophe() -> None:
    llm = ScriptedLLM(LLMResponse(text="I don\u2019t know that one."))
    result = run_agent(llm, [lookup_tool()], "q")
    assert result.answer == "I don\u2019t know that one."
