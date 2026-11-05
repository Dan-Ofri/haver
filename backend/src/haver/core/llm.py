"""Provider-neutral types for talking to a language model."""

from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class Message(BaseModel):
    role: Literal["user", "assistant", "tool"]
    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_call_id: str | None = None
    tool_name: str | None = None
    # Provider-specific payload a provider must get back unchanged on the next turn,
    # such as Gemini's thought signatures. Never interpreted by the core.
    provider_data: Any = Field(default=None, exclude=True)


class ToolSpec(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]


class LLMResponse(BaseModel):
    text: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    provider_data: Any = Field(default=None, exclude=True)


class LLM(Protocol):
    def complete(
        self, system: str, messages: list[Message], tools: list[ToolSpec]
    ) -> LLMResponse: ...
