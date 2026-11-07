"""The training domain."""

from pathlib import Path

from haver.core.plugin import Plugin
from haver.plugins.training.red_flags import RED_FLAGS

PLUGIN = Plugin(
    name="training", knowledge_dir=Path(__file__).parent / "knowledge", red_flags=RED_FLAGS
)
