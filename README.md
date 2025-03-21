# IAC Scanner

A Python-based Infrastructure as Code (IAC) scanner that functions as a Master Control Program (MCP) Server for LLMs, allowing for integration with various IAC scanning tools.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                             IAC Scanner                                  │
│                                                                         │
│  ┌─────────────┐    ┌─────────────────────────────────────────────────┐ │
│  │             │    │                Plugin System                     │ │
│  │  CLI / API  │    │                                                 │ │
│  │  Interface  │◄──►│  ┌──────────┐   ┌──────────┐   ┌───────────┐   │ │
│  │             │    │  │  Zodiac  │   │  Checkov │   │  Future   │   │ │
│  └─────────────┘    │  │  Plugin  │   │  Plugin  │   │  Plugins  │   │ │
│         ▲           │  └──────────┘   └──────────┘   └───────────┘   │ │
│         │           │         │             │              │         │ │
│         │           └─────────┼─────────────┼──────────────┼─────────┘ │
│         │                     │             │              │           │
│         │                     ▼             ▼              ▼           │
│         │           ┌─────────────────────────────────────────────────┐ │
│         └───────────┤                                                 │ │
│                     │             Results Aggregator                  │ │
│                     │                                                 │ │
│                     └─────────────────────────┬───────────────────────┘ │
│                                               │                         │
│                                               ▼                         │
│                     ┌─────────────────────────────────────────────────┐ │
│                     │                                                 │ │
│                     │           LLM Analysis (AWS Bedrock)            │ │
│                     │                                                 │ │
│                     └─────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

The IAC Scanner follows a plugin-based architecture where:
- The CLI/API interface provides user interaction
- The plugin system allows for integrating multiple scanning tools
- Results are aggregated from all plugins
- AWS Bedrock provides LLM analysis of scan results for enhanced insights

## Features

- Plugin architecture for integrating multiple IAC scanning tools
- LLM integration with AWS Bedrock for enhanced scanning capabilities
- Support for Terraform and CloudFormation scanning
- RESTful API for interacting with the scanner
- Comprehensive CLI for easy usage

## Integrated Tools

- [Zodiac](https://github.com/824728350/Zodiac): A tool for unearthing semantic checks for cloud Infrastructure-as-Code programs
- [Checkov](https://github.com/bridgecrewio/checkov): A static code analysis tool for infrastructure-as-code that detects security and compliance misconfigurations

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd iac-scanner

# Install dependencies
pip install -e .
```

## Usage Examples

### CLI Usage

#### Scanning IAC Code with All Available Plugins

```bash
# Scan a Terraform directory
iac-scanner scan --path /path/to/terraform/code

# Scan a CloudFormation template
iac-scanner scan --path /path/to/cloudformation/template.yaml
```

#### Specifying Plugins to Use

```bash
# Scan using only Checkov
iac-scanner scan --path /path/to/iac/code --tools checkov

# Scan using both Zodiac and Checkov
iac-scanner scan --path /path/to/iac/code --tools zodiac checkov
```

#### Saving Scan Results

```bash
# Save results in JSON format
iac-scanner scan --path /path/to/iac/code --output results.json

# Save results in YAML format
iac-scanner scan --path /path/to/iac/code --output results.yaml --format yaml
```

#### Listing Available Plugins

```bash
iac-scanner plugins
```

#### Starting the Server

```bash
# Start the server on default port (8000)
iac-scanner server start

# Start the server on a specific port
iac-scanner server start --port 9000
```

### API Usage

The IAC Scanner provides a RESTful API that you can interact with after starting the server:

#### List Available Plugins

```bash
curl http://localhost:8000/plugins
```

#### Run a Scan

```bash
curl -X POST \
  http://localhost:8000/scan \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/path/to/iac/code",
    "tools": ["zodiac", "checkov"]
  }'
```

### Programmatic Usage

You can also use the IAC Scanner programmatically in your Python applications:

```python
import asyncio
from pathlib import Path
from iac_scanner.plugins import discover_plugins, get_plugin

async def scan_example():
    # Discover available plugins
    discover_plugins()
    
    # Get the Checkov plugin
    checkov_plugin = get_plugin("checkov")()
    
    # Run a scan
    results = await checkov_plugin.scan(Path("/path/to/iac/code"))
    
    print(f"Scan completed with {len(results.get('failed_checks', []))} issues found")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(scan_example())
```

### Configuration

#### Environment Variables

The IAC Scanner supports configuration through environment variables:

```bash
# AWS Bedrock Configuration (for LLM analysis)
export AWS_REGION=us-east-1
export BEDROCK_MODEL_ID=anthropic.claude-v2
export AWS_PROFILE=default
# Or use direct credentials:
# export AWS_ACCESS_KEY_ID=your_access_key
# export AWS_SECRET_ACCESS_KEY=your_secret_key

# Zodiac Configuration
export ZODIAC_PATH=/path/to/zodiac
```

#### Configuration File (.env)

You can also create a `.env` file in the project root:

```
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-v2
ZODIAC_PATH=/path/to/zodiac
```

## Advanced Usage

### Custom Plugin Configuration

You can provide custom configuration for individual plugins:

```python
# Example of custom Checkov configuration
checkov_config = {
    "frameworks": ["terraform"],
    "skip_checks": ["CKV_AWS_24", "CKV_AWS_18"]
}

# Initialize plugin with config
checkov_plugin = get_plugin("checkov")(checkov_config)

# Run scan with custom config
results = await checkov_plugin.scan(path)
```

### Disabling LLM Processing

If you don't want to use AWS Bedrock for LLM processing:

```bash
# CLI method
iac-scanner scan --path /path/to/iac/code --no-llm

# API method
curl -X POST \
  http://localhost:8000/scan \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/path/to/iac/code",
    "use_llm": false
  }'
```

## Examples

For detailed examples, check out the `examples` directory which contains:

- Sample Terraform and CloudFormation templates
- Shell scripts demonstrating CLI usage
- Python scripts showing programmatic usage
- Detailed README explaining the examples

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## License

MIT 