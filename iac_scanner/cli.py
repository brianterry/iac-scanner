"""Command-line interface for the IAC Scanner."""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from dotenv import load_dotenv

from iac_scanner import __version__
from iac_scanner.core.server import Server, ServerConfig
from iac_scanner.plugins import discover_plugins, get_plugin, get_all_plugins


# Load environment variables from .env file if present
load_dotenv()


@click.group()
@click.version_option(version=__version__)
def main():
    """IAC Scanner - A tool for scanning Infrastructure as Code."""
    pass


@main.group()
def server():
    """Server management commands."""
    pass


@server.command("start")
@click.option("--host", default="localhost", help="Host to bind the server to")
@click.option("--port", default=8000, help="Port to bind the server to")
@click.option("--log-level", default="INFO", help="Logging level")
def start_server(host: str, port: int, log_level: str):
    """Start the server."""
    config = ServerConfig(
        host=host,
        port=port,
        log_level=log_level,
        llm_config={
            "aws_region": os.environ.get("AWS_REGION", "us-east-1"),
            "model_id": os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-v2"),
            "aws_profile": os.environ.get("AWS_PROFILE"),
            "aws_access_key": os.environ.get("AWS_ACCESS_KEY_ID"),
            "aws_secret_key": os.environ.get("AWS_SECRET_ACCESS_KEY"),
        },
    )
    
    server = Server(config)
    click.echo(f"Starting server on {host}:{port}")
    server.start()


@main.command("scan")
@click.option("--path", "-p", required=True, help="Path to the IAC code to scan")
@click.option("--tools", "-t", multiple=True, help="Tools to use for scanning")
@click.option("--output", "-o", help="Output file for scan results")
@click.option("--format", "-f", default="json", type=click.Choice(["json", "yaml"]), help="Output format")
def scan(path: str, tools: List[str], output: Optional[str], format: str):
    """Scan IAC code."""
    async def run_scan():
        scan_path = Path(path)
        if not scan_path.exists():
            click.echo(f"Error: Path not found: {path}", err=True)
            sys.exit(1)
        
        # Discover available plugins
        discover_plugins()
        
        # Determine which tools to use
        tool_names = list(tools) if tools else list(get_all_plugins().keys())
        click.echo(f"Running scan on {path} with tools: {', '.join(tool_names)}")
        
        # Run the scan with each tool
        results = {}
        errors = {}
        
        for tool_name in tool_names:
            plugin_class = get_plugin(tool_name)
            if not plugin_class:
                errors[tool_name] = f"Plugin not found: {tool_name}"
                continue
            
            try:
                click.echo(f"Running scan with {tool_name}...")
                plugin = plugin_class()
                if not await plugin.validate_config():
                    errors[tool_name] = "Invalid plugin configuration"
                    continue
                
                scan_result = await plugin.scan(scan_path)
                results[tool_name] = scan_result
            except Exception as e:
                errors[tool_name] = str(e)
        
        # Prepare the output
        scan_output = {
            "success": len(errors) == 0,
            "results": results,
            "errors": errors or None
        }
        
        # Output the results
        if output:
            output_path = Path(output)
            if format == "json":
                with output_path.open("w") as f:
                    json.dump(scan_output, f, indent=2)
            elif format == "yaml":
                import yaml
                with output_path.open("w") as f:
                    yaml.dump(scan_output, f)
            click.echo(f"Scan results written to {output}")
        else:
            if format == "json":
                click.echo(json.dumps(scan_output, indent=2))
            elif format == "yaml":
                import yaml
                click.echo(yaml.dump(scan_output))
    
    # Run the async function
    asyncio.run(run_scan())


@main.command("plugins")
def list_plugins():
    """List available plugins."""
    async def run_list_plugins():
        # Discover available plugins
        discover_plugins()
        
        plugins = get_all_plugins()
        click.echo(f"Found {len(plugins)} plugins:")
        
        for name, plugin_class in plugins.items():
            plugin = plugin_class()
            capabilities = await plugin.get_capabilities()
            click.echo(f"\n{name}:")
            click.echo(f"  Description: {capabilities.get('description', 'N/A')}")
            click.echo(f"  Supports: {', '.join(capabilities.get('supports', []))}")
            click.echo(f"  Features: {', '.join(capabilities.get('features', []))}")
    
    # Run the async function
    asyncio.run(run_list_plugins())


if __name__ == "__main__":
    main() 