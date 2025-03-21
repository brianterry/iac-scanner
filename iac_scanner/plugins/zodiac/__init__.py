"""Zodiac plugin for IAC scanner."""

from iac_scanner.plugins.zodiac.plugin import ZodiacPlugin
from iac_scanner.plugins import register_plugin

# Register the plugin
register_plugin("zodiac", ZodiacPlugin) 