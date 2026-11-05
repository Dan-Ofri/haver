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
            name=self.name,
            description=self.description,
            parameters=self.args_model.model_json_schema(),
        )
