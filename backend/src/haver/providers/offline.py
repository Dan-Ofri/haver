"""A deterministic stand-in for a real model, used without an API key and in CI.

It searches once with the question and answers with the first paragraph of the top result.
It shows that every layer is wired together, not that answers are good.
"""

from typing import Any

from haver.core.llm import LLMResponse, Message, ToolCall, ToolSpec

TOP_DOCUMENT_PREFIX = '<document id="'


class OfflineLLM:
    def complete(self, system: str, messages: list[Message], tools: list[ToolSpec]) -> LLMResponse:
        last = messages[-1]
        if last.role == "user":
            search = ToolCall(id="1", name="search_knowledge", arguments={"query": last.content})
            return LLMResponse(tool_calls=[search])
        answer: dict[str, Any]
        if not last.content.startswith(TOP_DOCUMENT_PREFIX):
            answer = {"missing": "Nothing in my knowledge base covers that."}
        else:
            doc_id = last.content.removeprefix(TOP_DOCUMENT_PREFIX).split('"', 1)[0]
            body = last.content.split(">\n", 1)[1].split("\n</document>", 1)[0]
            claim = {"text": body.split("\n\n", 1)[0], "sources": [doc_id]}
            answer = {"claims": [claim]}
        return LLMResponse(tool_calls=[ToolCall(id="2", name="respond", arguments=answer)])
