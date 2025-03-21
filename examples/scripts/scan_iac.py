#!/usr/bin/env python3
"""
Example script for programmatically using the IAC Scanner.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Ensure we can import from the iac_scanner package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from iac_scanner.plugins import discover_plugins, get_plugin
from iac_scanner.core.llm import LLMClient


async def scan_iac_directory(path, tools=None, use_llm=True):
    """Scan an IAC directory using the specified tools."""
    
    # Convert path to Path object
    scan_path = Path(path)
    if not scan_path.exists():
        print(f"Error: Path not found: {path}")
        return None
    
    # Discover available plugins
    discover_plugins()
    
    # Determine which tools to use
    if tools is None:
        from iac_scanner.plugins import get_all_plugins
        tool_names = list(get_all_plugins().keys())
    else:
        tool_names = tools
    
    print(f"Running scan on {path} with tools: {', '.join(tool_names)}")
    
    # Run the scan with each tool
    results = {}
    errors = {}
    
    for tool_name in tool_names:
        plugin_class = get_plugin(tool_name)
        if not plugin_class:
            errors[tool_name] = f"Plugin not found: {tool_name}"
            continue
        
        try:
            print(f"Running scan with {tool_name}...")
            plugin = plugin_class()
            if not await plugin.validate_config():
                errors[tool_name] = "Invalid plugin configuration"
                continue
            
            scan_result = await plugin.scan(scan_path)
            results[tool_name] = scan_result
        except Exception as e:
            errors[tool_name] = str(e)
    
    # Process results with LLM if requested
    if use_llm:
        llm_config = {
            "aws_region": os.environ.get("AWS_REGION", "us-east-1"),
            "model_id": os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-v2"),
            "aws_profile": os.environ.get("AWS_PROFILE"),
            "aws_access_key": os.environ.get("AWS_ACCESS_KEY_ID"),
            "aws_secret_key": os.environ.get("AWS_SECRET_ACCESS_KEY"),
        }
        
        llm_client = LLMClient(llm_config)
        if llm_client.is_available():
            try:
                print("Processing results with LLM...")
                processed_results = await llm_client.process_scan_results(results)
                results = processed_results
            except Exception as e:
                print(f"Error processing results with LLM: {e}")
    
    # Prepare the output
    scan_output = {
        "success": len(errors) == 0,
        "results": results,
        "errors": errors or None
    }
    
    return scan_output


async def main():
    """Main function."""
    
    # Set default paths to scan
    terraform_path = Path(__file__).parent.parent / "terraform" / "simple-aws"
    cloudformation_path = Path(__file__).parent.parent / "cloudformation" / "simple-aws"
    
    # Scan Terraform code with both Zodiac and Checkov
    print("Scanning Terraform code with multiple tools...")
    terraform_results = await scan_iac_directory(terraform_path, tools=["zodiac", "checkov"])
    
    # Save Terraform results
    with open("terraform_scan_results.json", "w") as f:
        json.dump(terraform_results, f, indent=2)
    print("Terraform scan complete. Results saved to terraform_scan_results.json")
    
    # Scan CloudFormation template with both Zodiac and Checkov
    print("\nScanning CloudFormation template with multiple tools...")
    cloudformation_results = await scan_iac_directory(cloudformation_path, tools=["zodiac", "checkov"])
    
    # Save CloudFormation results
    with open("cloudformation_scan_results.json", "w") as f:
        json.dump(cloudformation_results, f, indent=2)
    print("CloudFormation scan complete. Results saved to cloudformation_scan_results.json")
    
    # Example of scanning with just Checkov and customizing its configuration
    print("\nScanning Terraform code with just Checkov and custom config...")
    checkov_config = {
        "checkov": {
            "frameworks": ["terraform"],
            "skip_checks": ["CKV_AWS_24", "CKV_AWS_18"]  # Skip specific checks
        }
    }
    terraform_checkov_results = await scan_iac_directory(
        terraform_path, 
        tools=["checkov"],
        use_llm=False  # Don't use LLM for this scan
    )
    
    # Save Checkov-specific results
    with open("terraform_checkov_results.json", "w") as f:
        json.dump(terraform_checkov_results, f, indent=2)
    print("Checkov-specific scan complete. Results saved to terraform_checkov_results.json")


if __name__ == "__main__":
    # Set up environment variables if not already set
    if "AWS_REGION" not in os.environ:
        os.environ["AWS_REGION"] = "us-east-1"
    if "BEDROCK_MODEL_ID" not in os.environ:
        os.environ["BEDROCK_MODEL_ID"] = "anthropic.claude-v2"
    
    # Run the async main function
    asyncio.run(main()) 