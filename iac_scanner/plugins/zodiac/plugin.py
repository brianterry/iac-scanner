"""Zodiac plugin implementation for IAC scanner."""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
import git
import yaml

from iac_scanner.plugins.base import BasePlugin


class ZodiacPlugin(BasePlugin):
    """Plugin for integrating with Zodiac IAC semantic checking tool."""
    
    name = "zodiac"
    description = "Plugin for Zodiac - Unearthing Semantic Checks for Cloud IAC"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Zodiac plugin.
        
        Args:
            config: Configuration dictionary. Supported keys:
                - zodiac_repo: URL to the Zodiac Git repository
                - zodiac_path: Local path to the Zodiac installation
        """
        super().__init__(config)
        self.zodiac_path = self.config.get("zodiac_path")
        self.zodiac_repo = self.config.get(
            "zodiac_repo", "https://github.com/824728350/Zodiac.git"
        )
    
    async def validate_config(self) -> bool:
        """Validate the plugin configuration.
        
        Ensures that either zodiac_path is set to a valid Zodiac installation
        or that we can clone the repository.
        
        Returns:
            True if the configuration is valid, False otherwise
        """
        if not self.zodiac_path:
            # If no path is specified, we'll clone on demand
            return True
        
        # Check if the specified path contains a valid Zodiac installation
        zodiac_path = Path(self.zodiac_path)
        return (
            zodiac_path.exists()
            and (zodiac_path / "main.py").exists()
        )
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get the capabilities of this plugin.
        
        Returns:
            A dictionary describing the capabilities of this plugin
        """
        return {
            "name": self.name,
            "description": self.description,
            "supports": ["terraform", "cloudformation"],
            "features": ["semantic_checks", "invariant_mining"]
        }
    
    async def _ensure_zodiac_available(self) -> Path:
        """Ensure that Zodiac is available locally.
        
        If zodiac_path is specified, it will be used. Otherwise, Zodiac
        will be cloned from the repository to a temporary directory.
        
        Returns:
            Path to the Zodiac installation
        """
        if self.zodiac_path and await self.validate_config():
            return Path(self.zodiac_path)
        
        # Clone Zodiac to a temporary directory
        tmp_dir = Path(tempfile.mkdtemp())
        git.Repo.clone_from(self.zodiac_repo, tmp_dir)
        
        # Set the path for future use
        self.zodiac_path = str(tmp_dir)
        return tmp_dir
    
    async def scan(self, path: Path) -> Dict[str, Any]:
        """Scan a directory or file using Zodiac.
        
        Args:
            path: Path to the directory or file to scan
            
        Returns:
            A dictionary containing scan results
        """
        zodiac_path = await self._ensure_zodiac_available()
        
        # Create a temporary file to store the scan results
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmp_file:
            output_file = tmp_file.name
        
        try:
            # Run Zodiac on the specified path
            # Note: This is a simplified example. The actual command might differ.
            result = subprocess.run(
                [
                    "python",
                    str(zodiac_path / "main.py"),
                    "--input", str(path),
                    "--output", output_file
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the output
            if os.path.exists(output_file):
                with open(output_file, "r") as f:
                    scan_results = yaml.safe_load(f)
            else:
                scan_results = {}
            
            return {
                "success": True,
                "results": scan_results,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": e.stdout,
                "stderr": e.stderr
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            # Clean up the temporary file
            if os.path.exists(output_file):
                os.unlink(output_file) 