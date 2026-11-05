"""The sleep domain."""

from pathlib import Path

from haver.core.plugin import Plugin

PLUGIN = Plugin(name="sleep", knowledge_dir=Path(__file__).parent / "knowledge")
