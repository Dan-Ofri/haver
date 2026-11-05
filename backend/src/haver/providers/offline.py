"""A deterministic stand-in for a real model, used without an API key and in CI.

It searches once with the question and answers from the top result. It shows that every
layer is wired together, not that answers are good.
"""

from haver.core.llm import LLMResponse, Message, ToolCall, ToolSpec

TOP_DOCUMENT_PREFIX = '<document id="'


class OfflineLLM:
    def complete(self, system: str, messages: list[Message], tools: list[ToolSpec]) -> LLMResponse:
        last = messages[-1]
        if last.role == "user":
            return LLMResponse(
                tool_calls=[
                    ToolCall(
                        id="call-1", name="search_knowledge", arguments={"query": last.content}
                    )
                ]
            )
        if not last.content.startswith(TOP_DOCUMENT_PREFIX):
            return LLMResponse(text="I don't know. Nothing in my knowledge base covers that.")
        doc_id = last.content.removeprefix(TOP_DOCUMENT_PREFIX).split('"', 1)[0]
        body = last.content.split(">\n", 1)[1].split("\n</document>", 1)[0]
        first_paragraph = body.split("\n\n", 1)[0]
        return LLMResponse(text=f"{first_paragraph} [doc:{doc_id}]")
