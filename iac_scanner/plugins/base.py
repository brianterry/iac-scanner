"""Base plugin class for IAC scanner plugins."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional


class BasePlugin(ABC):
    """Base class for all IAC scanner plugins."""
    
    name: str = "base"
    description: str = "Base plugin class for IAC scanner"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the plugin.
        
        Args:
            config: Configuration parameters for the plugin
        """
        self.config = config or {}
    
    @abstractmethod
    async def scan(self, path: Path) -> Dict[str, Any]:
        """Scan a directory or file for IAC issues.
        
        Args:
            path: Path to the directory or file to scan
            
        Returns:
            A dictionary containing scan results
        """
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get the capabilities of this plugin.
        
        Returns:
            A dictionary describing the capabilities of this plugin
        """
        pass
    
    @abstractmethod
    async def validate_config(self) -> bool:
        """Validate the plugin configuration.
        
        Returns:
            True if the configuration is valid, False otherwise
        """
        pass 