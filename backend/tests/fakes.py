from haver.core.llm import LLMResponse, Message, ToolSpec


class ScriptedLLM:
    """Returns prepared responses in order and records what it was sent.

    A call without tools is the safety check: it gets `triage` back and does not use up a
    prepared response, so agent tests need not script it.
    """

    def __init__(self, *responses: LLMResponse, triage: str = "none") -> None:
        self._responses = list(responses)
        self._triage = triage
        self.calls: list[list[Message]] = []
        self.tools: list[list[ToolSpec]] = []
        self.triage_calls: list[str] = []

    def complete(self, system: str, messages: list[Message], tools: list[ToolSpec]) -> LLMResponse:
        if not tools:
            self.triage_calls.append(messages[-1].content)
            return LLMResponse(text=self._triage, input_tokens=10, output_tokens=1)
        self.calls.append(list(messages))
        self.tools.append(list(tools))
        return self._responses.pop(0)
