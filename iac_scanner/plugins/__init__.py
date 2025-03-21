"""Plugin architecture for IAC scanning tools."""

from importlib import import_module
from typing import Dict, List, Type

from iac_scanner.plugins.base import BasePlugin

_plugins: Dict[str, Type[BasePlugin]] = {}

def register_plugin(name: str, plugin_class: Type[BasePlugin]):
    """Register a plugin with the system."""
    _plugins[name] = plugin_class
    
def get_plugin(name: str) -> Type[BasePlugin]:
    """Get a plugin by name."""
    return _plugins.get(name)

def get_all_plugins() -> Dict[str, Type[BasePlugin]]:
    """Return all registered plugins."""
    return _plugins

def discover_plugins():
    """Discover and register all available plugins."""
    # Import built-in plugins
    from iac_scanner.plugins import zodiac
    from iac_scanner.plugins import checkov
    
    # Additional plugin discovery logic could be added here
    # For example, discovering plugins from a specific directory 