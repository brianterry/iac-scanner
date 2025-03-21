"""Checkov plugin implementation for IAC scanner."""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

try:
    from checkov.main import Runner
except ImportError:
    Runner = None

from iac_scanner.plugins.base import BasePlugin


class CheckovPlugin(BasePlugin):
    """Plugin for integrating with Checkov static analysis tool."""
    
    name = "checkov"
    description = "Plugin for Checkov - Static code analysis tool for infrastructure-as-code"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Checkov plugin.
        
        Args:
            config: Configuration dictionary. Supported keys:
                - frameworks: List of frameworks to scan (e.g., terraform, cloudformation)
                - checks: List of specific checks to run
                - skip_checks: List of checks to skip
                - use_api: Whether to use the Checkov Python API or CLI
        """
        super().__init__(config)
        self.use_api = self.config.get("use_api", True)
        self.frameworks = self.config.get("frameworks", ["all"])
        self.checks = self.config.get("checks", [])
        self.skip_checks = self.config.get("skip_checks", [])
    
    async def validate_config(self) -> bool:
        """Validate the plugin configuration.
        
        Returns:
            True if Checkov is available, False otherwise
        """
        # If using API, check if Checkov is available as a module
        if self.use_api and Runner is None:
            return False
        
        # If using CLI, check if Checkov is available as a command
        if not self.use_api:
            try:
                result = subprocess.run(
                    ["checkov", "--version"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                return result.returncode == 0
            except FileNotFoundError:
                return False
        
        return True
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get the capabilities of this plugin.
        
        Returns:
            A dictionary describing the capabilities of this plugin
        """
        return {
            "name": self.name,
            "description": self.description,
            "supports": [
                "terraform", 
                "cloudformation",
                "kubernetes",
                "docker",
                "arm",
                "bicep",
                "helm",
                "serverless"
            ],
            "features": [
                "security_checks",
                "compliance_checks",
                "misconfigurations"
            ]
        }
    
    async def scan(self, path: Path) -> Dict[str, Any]:
        """Scan a directory or file using Checkov.
        
        Args:
            path: Path to the directory or file to scan
            
        Returns:
            A dictionary containing scan results
        """
        if self.use_api and Runner is not None:
            return await self._scan_with_api(path)
        else:
            return await self._scan_with_cli(path)
    
    async def _scan_with_api(self, path: Path) -> Dict[str, Any]:
        """Scan using Checkov's Python API.
        
        Args:
            path: Path to the directory or file to scan
            
        Returns:
            A dictionary containing scan results
        """
        try:
            # Create arguments for the Runner
            runner_args = {
                "directory": str(path) if path.is_dir() else None,
                "file": str(path) if path.is_file() else None,
                "external_checks_dir": None,
                "external_modules_download_path": None,
                "framework": self.frameworks,
                "skip_check": self.skip_checks,
                "check": self.checks,
                "runner_filter": None,
                "excluded_paths": [],
            }
            
            # Initialize the runner
            runner = Runner()
            
            # Run the scan
            results = runner.run(**runner_args)
            
            # Process results
            checks_results = results.get("results", {})
            
            # Format the results
            formatted_results = {
                "success": True,
                "failed_checks": [],
                "passed_checks": [],
                "skipped_checks": [],
                "summary": {
                    "failed": 0,
                    "passed": 0,
                    "skipped": 0,
                    "total": 0,
                }
            }
            
            # Process each framework's results
            for framework_name, framework_results in checks_results.items():
                # Add failed checks
                for failed_check in framework_results.get("failed_checks", []):
                    formatted_results["failed_checks"].append({
                        "id": failed_check.check_id,
                        "name": failed_check.check_name,
                        "resource": failed_check.resource,
                        "file_path": failed_check.file_path,
                        "file_line_range": failed_check.file_line_range,
                        "guideline": failed_check.guideline,
                        "severity": failed_check.severity,
                        "framework": framework_name,
                    })
                    formatted_results["summary"]["failed"] += 1
                
                # Add passed checks
                for passed_check in framework_results.get("passed_checks", []):
                    formatted_results["passed_checks"].append({
                        "id": passed_check.check_id,
                        "name": passed_check.check_name,
                        "resource": passed_check.resource,
                        "file_path": passed_check.file_path,
                        "framework": framework_name,
                    })
                    formatted_results["summary"]["passed"] += 1
                
                # Add skipped checks
                for skipped_check in framework_results.get("skipped_checks", []):
                    formatted_results["skipped_checks"].append({
                        "id": skipped_check.check_id,
                        "name": skipped_check.check_name,
                        "resource": skipped_check.resource,
                        "file_path": skipped_check.file_path,
                        "framework": framework_name,
                    })
                    formatted_results["summary"]["skipped"] += 1
            
            formatted_results["summary"]["total"] = (
                formatted_results["summary"]["failed"] +
                formatted_results["summary"]["passed"] +
                formatted_results["summary"]["skipped"]
            )
            
            return formatted_results
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _scan_with_cli(self, path: Path) -> Dict[str, Any]:
        """Scan using Checkov's CLI.
        
        Args:
            path: Path to the directory or file to scan
            
        Returns:
            A dictionary containing scan results
        """
        try:
            # Create a temporary file to store the scan results
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
                output_file = tmp_file.name
            
            # Build the command
            cmd = ["checkov"]
            
            if path.is_dir():
                cmd.extend(["-d", str(path)])
            else:
                cmd.extend(["-f", str(path)])
            
            # Add frameworks to scan
            if self.frameworks and "all" not in self.frameworks:
                for framework in self.frameworks:
                    cmd.extend(["--framework", framework])
            
            # Add checks to run
            for check in self.checks:
                cmd.extend(["--check", check])
            
            # Add checks to skip
            for check in self.skip_checks:
                cmd.extend(["--skip-check", check])
            
            # Add output format
            cmd.extend(["--output", "json", "--output-file", output_file])
            
            # Run Checkov
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            # Parse the results
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                with open(output_file, "r") as f:
                    checkov_results = json.load(f)
            else:
                # If no JSON was produced, create a basic structure with the stderr
                checkov_results = {
                    "success": result.returncode == 0,
                    "error": result.stderr if result.returncode != 0 else None,
                    "summary": {}
                }
            
            # Clean up the temporary file
            if os.path.exists(output_file):
                os.unlink(output_file)
            
            return checkov_results
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            } 