"""Tools the agent can call. Arguments are validated before a tool runs."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from haver.core.llm import ToolSpec


class Source(BaseModel):
    """A piece of content a tool returned, which an answer may cite."""

    id: str
    title: str
    url: str


@dataclass
class ToolOutput:
    content: str
    sources: list[Source] = field(default_factory=list)


@dataclass
class Tool:
    name: str
    description: str
    args_model: type[BaseModel]
    run: Callable[[Any], ToolOutput]

    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.name, description=self.description, parameters=json_schema(self.args_model)
        )


def json_schema(model: type[BaseModel]) -> dict[str, Any]:
    """The model's JSON schema with every $ref inlined, since not every provider resolves them."""
    schema = model.model_json_schema()
    definitions = schema.pop("$defs", {})

    def inline(node: Any) -> Any:
        if isinstance(node, dict):
            if "$ref" in node:
                return inline(definitions[node["$ref"].rsplit("/", 1)[-1]])
            return {key: inline(value) for key, value in node.items()}
        if isinstance(node, list):
            return [inline(item) for item in node]
        return node

    result: dict[str, Any] = inline(schema)
    return result
