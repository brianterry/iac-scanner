"""Basic tests for the IAC Scanner."""

import os
import sys
import pytest
from pathlib import Path

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from iac_scanner.plugins.base import BasePlugin
from iac_scanner.plugins import register_plugin, get_plugin


class MockPlugin(BasePlugin):
    """Mock plugin for testing."""
    
    name = "mock"
    description = "Mock plugin for testing"
    
    async def scan(self, path):
        """Mock scan method."""
        return {
            "success": True,
            "results": {
                "issues": []
            }
        }
    
    async def get_capabilities(self):
        """Mock get_capabilities method."""
        return {
            "name": self.name,
            "description": self.description,
            "supports": ["terraform", "cloudformation"],
            "features": ["mock_scanning"]
        }
    
    async def validate_config(self):
        """Mock validate_config method."""
        return True


def test_plugin_registration():
    """Test plugin registration."""
    # Register the mock plugin
    register_plugin("mock", MockPlugin)
    
    # Get the plugin
    plugin_class = get_plugin("mock")
    
    # Check that we got the right plugin
    assert plugin_class is not None
    assert plugin_class is MockPlugin
    
    # Create an instance
    plugin = plugin_class()
    
    # Check the instance
    assert plugin.name == "mock"
    assert plugin.description == "Mock plugin for testing"


@pytest.mark.asyncio
async def test_plugin_capabilities():
    """Test plugin capabilities."""
    # Register the mock plugin
    register_plugin("mock", MockPlugin)
    
    # Get the plugin
    plugin_class = get_plugin("mock")
    plugin = plugin_class()
    
    # Get capabilities
    capabilities = await plugin.get_capabilities()
    
    # Check capabilities
    assert capabilities["name"] == "mock"
    assert capabilities["description"] == "Mock plugin for testing"
    assert "terraform" in capabilities["supports"]
    assert "cloudformation" in capabilities["supports"]
    assert "mock_scanning" in capabilities["features"]


@pytest.mark.asyncio
async def test_plugin_scan():
    """Test plugin scan."""
    # Register the mock plugin
    register_plugin("mock", MockPlugin)
    
    # Get the plugin
    plugin_class = get_plugin("mock")
    plugin = plugin_class()
    
    # Run a scan
    scan_result = await plugin.scan(Path("."))
    
    # Check scan result
    assert scan_result["success"] is True
    assert "results" in scan_result
    assert "issues" in scan_result["results"] 