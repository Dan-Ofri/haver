"""Google Gemini through the google-genai SDK."""

from google import genai
from google.genai import types

from haver.core.llm import LLMResponse, Message, ToolCall, ToolSpec


class GeminiLLM:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def complete(self, system: str, messages: list[Message], tools: list[ToolSpec]) -> LLMResponse:
        config = _config(system, tools)
        response = self._client.models.generate_content(
            model=self._model, contents=_to_contents(messages), config=config
        )
        calls = [
            ToolCall(id=call.id or "", name=call.name or "", arguments=call.args or {})
            for call in response.function_calls or []
        ]
        usage = response.usage_metadata
        content = response.candidates[0].content if response.candidates else None
        return LLMResponse(
            text="" if calls else (response.text or ""),
            tool_calls=calls,
            input_tokens=(usage.prompt_token_count or 0) if usage else 0,
            # Thinking tokens are billed as output, so they count.
            output_tokens=(
                (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)
                if usage
                else 0
            ),
            provider_data=content,
        )


def _config(system: str, tools: list[ToolSpec]) -> types.GenerateContentConfig:
    declarations = [
        types.FunctionDeclaration(
            name=t.name, description=t.description, parameters_json_schema=t.parameters
        )
        for t in tools
    ]
    return types.GenerateContentConfig(
        system_instruction=system,
        # A call with no tools, such as the safety check, sends none: an empty list is rejected.
        tools=[types.Tool(function_declarations=declarations)] if declarations else None,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )


def _to_contents(messages: list[Message]) -> list[types.Content]:
    contents: list[types.Content] = []
    for message in messages:
        if message.role == "user":
            text = types.Part.from_text(text=message.content)
            contents.append(types.Content(role="user", parts=[text]))
        elif message.role == "assistant":
            # Send the model's own turn back unchanged: it carries thought signatures.
            if isinstance(message.provider_data, types.Content):
                if message.provider_data.parts:  # an empty turn (blocked, malformed) is skipped
                    contents.append(message.provider_data)
            else:
                parts = [
                    types.Part.from_function_call(name=c.name, args=c.arguments)
                    for c in message.tool_calls
                ]
                if parts:
                    contents.append(types.Content(role="model", parts=parts))
        else:
            part = types.Part(
                function_response=types.FunctionResponse(
                    id=message.tool_call_id or None,
                    name=message.tool_name or "",
                    response={"result": message.content},
                )
            )
            previous = contents[-1] if contents else None
            if previous and previous.parts and previous.parts[0].function_response:
                # Answers to calls made in one turn go back together, in one turn.
                previous.parts.append(part)
            else:
                contents.append(types.Content(role="user", parts=[part]))
    return contents
