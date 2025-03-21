"""Checkov plugin for IAC scanner."""

from iac_scanner.plugins.checkov.plugin import CheckovPlugin
from iac_scanner.plugins import register_plugin

# Register the plugin
register_plugin("checkov", CheckovPlugin) 