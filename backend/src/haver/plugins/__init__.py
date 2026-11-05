"""Domain plugins. The app registers them here; the core never imports this package."""

from haver.core.plugin import Plugin
from haver.plugins import sleep, training

PLUGINS: list[Plugin] = [training.PLUGIN, sleep.PLUGIN]
