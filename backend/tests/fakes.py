from haver.core.llm import LLMResponse, Message, ToolSpec


class ScriptedLLM:
    """Returns prepared responses in order and records what it was sent."""

    def __init__(self, *responses: LLMResponse) -> None:
        self._responses = list(responses)
        self.calls: list[list[Message]] = []

    def complete(self, system: str, messages: list[Message], tools: list[ToolSpec]) -> LLMResponse:
        self.calls.append(list(messages))
        return self._responses.pop(0)
