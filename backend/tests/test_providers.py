import pytest
from google.genai import types
from pydantic import SecretStr

from haver.config import Settings
from haver.core.llm import Message, ToolCall
from haver.providers import build_embedder, build_llm
from haver.providers.gemini import _to_contents
from haver.providers.offline import OfflineLLM
from haver.providers.offline_embedder import HashingEmbedder


def test_defaults_to_the_offline_model() -> None:
    assert isinstance(build_llm(Settings(_env_file=None)), OfflineLLM)


def test_gemini_without_a_key_fails_clearly() -> None:
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        build_llm(Settings(_env_file=None, llm_provider="gemini"))


def test_gemini_with_a_key_builds() -> None:
    settings = Settings(_env_file=None, llm_provider="gemini", gemini_api_key=SecretStr("k"))
    assert type(build_llm(settings)).__name__ == "GeminiLLM"


def test_gemini_gets_the_model_turn_back_unchanged_and_tool_answers_together() -> None:
    model_turn = types.Content(role="model", parts=[types.Part.from_text(text="thinking")])
    calls = [ToolCall(id="a", name="t", arguments={}), ToolCall(id="b", name="t", arguments={})]
    contents = _to_contents(
        [
            Message(role="user", content="q"),
            Message(role="assistant", tool_calls=calls, provider_data=model_turn),
            Message(role="tool", content="r1", tool_call_id="a", tool_name="t"),
            Message(role="tool", content="r2", tool_call_id="b", tool_name="t"),
        ]
    )
    assert [c.role for c in contents] == ["user", "model", "user"]
    assert contents[1] is model_turn
    assert contents[2].parts is not None and len(contents[2].parts) == 2


def test_gemini_skips_empty_model_turns() -> None:
    contents = _to_contents(
        [
            Message(role="user", content="q"),
            Message(role="assistant", provider_data=types.Content(role="model", parts=None)),
            Message(role="assistant"),
            Message(role="user", content="Reply by calling the `respond` tool."),
        ]
    )
    assert [c.role for c in contents] == ["user", "user"]


def test_build_embedder_matches_the_provider(settings: Settings) -> None:
    assert isinstance(build_embedder(settings), HashingEmbedder)
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        build_embedder(settings.model_copy(update={"llm_provider": "gemini"}))
