"""A deterministic stand-in for a real model, used without an API key and in CI.

It searches once with the question and answers with the first paragraph of the top result.
It shows that every layer is wired together, not that answers are good.
Asked to classify without tools (the safety check), it answers "none": it has no judgment, so
safety without a real model rests on the patterns in code.
"""

from typing import Any

from haver.core.llm import LLMResponse, Message, ToolCall, ToolSpec

TOP_DOCUMENT_PREFIX = '<document id="'


def last_question(messages: list[Message]) -> str:
    return next(m.content for m in reversed(messages) if m.role == "user")


class OfflineLLM:
    def complete(self, system: str, messages: list[Message], tools: list[ToolSpec]) -> LLMResponse:
        if not tools:
            return LLMResponse(text="none")
        last = messages[-1]
        if last.role == "user":
            search = ToolCall(id="1", name="search_knowledge", arguments={"query": last.content})
            return LLMResponse(tool_calls=[search])
        answer: dict[str, Any]
        if not last.content.startswith(TOP_DOCUMENT_PREFIX):
            topic = last_question(messages).strip().rstrip("?.!") or "that"
            answer = {"missing_topic": topic[:60]}
        else:
            doc_id = last.content.removeprefix(TOP_DOCUMENT_PREFIX).split('"', 1)[0]
            body = last.content.split(">\n", 1)[1].split("\n</document>", 1)[0]
            claim = {"text": body.split("\n\n", 1)[0], "sources": [doc_id]}
            answer = {"claims": [claim]}
        return LLMResponse(tool_calls=[ToolCall(id="2", name="respond", arguments=answer)])
