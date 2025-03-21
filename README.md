# IAC Scanner

A tool for scanning Infrastructure as Code (IaC) files for security issues, using a plugin architecture and optionally leveraging LLMs for enhanced analysis.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    IAC Scanner                           │
├─────────────────┬─────────────────┬────────────────────┐│
│  CLI/API         │  Plugin System   │  MCP Server        ││
│  Interface       │                 │                    ││
│                 │  ┌─────────────┐ │  ┌───────────────┐ ││
│  - Scan         │  │ Zodiac      │ │  │ REST API      │ ││
│  - Configure    │  │ Plugin      │ │  │               │ ││
│  - Results      │  └─────────────┘ │  │ - Plugins     │ ││
│                 │  ┌─────────────┐ │  │ - Scan        │ ││
│                 │  │ Checkov     │ │  │ - Results     │ ││
│                 │  │ Plugin      │ │  └───────────────┘ ││
│                 │  └─────────────┘ │                    ││
├─────────────────┴─────────────────┼────────────────────┤│
│  Results Aggregator                │ LLM Integration    ││
│                                   │                    ││
│  - Combine findings               │ - AWS Bedrock      ││
│  - Normalize formats              │ - Analysis         ││
│  - Generate reports               │ - Recommendations  ││
└───────────────────────────────────┴────────────────────┘
```

## Features

- **Plugin Architecture**: Easily extend with new scanning tools
- **LLM Integration**: Use AWS Bedrock for enhanced analysis (optional)
- **Terraform & CloudFormation**: Support for major IaC formats
- **RESTful API**: Serve as a Master Control Program (MCP) for other tools or LLMs

## Usage

### CLI Usage

```bash
# Basic scan
iac-scanner scan --directory /path/to/iac/code

# Specify plugins
iac-scanner scan --directory /path/to/iac/code --tools zodiac checkov

# Save results to file
iac-scanner scan --directory /path/to/iac/code --output results.json

# Start MCP server
iac-scanner server start
```

### API Usage

```bash
# Start the server
iac-scanner server start

# Then in another terminal or via HTTP client:
curl -X POST http://localhost:8000/scan \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/iac/code", "tools": ["zodiac", "checkov"]}'
```

### Programmatic Usage

```python
from iac_scanner.cli.scan import scan_directory

# Scan a directory
results = scan_directory(
    directory="/path/to/iac/code",
    tools=["zodiac", "checkov"],
    output_file="results.json"
)

# Process results
for tool, findings in results["findings"].items():
    print(f"Found {len(findings)} issues with {tool}")
```

## Configuration

Configure the scanner using environment variables or a `.env` file:

```
# AWS Bedrock configuration for LLM analysis
BEDROCK_MODEL_ID=anthropic.claude-v2
AWS_REGION=us-east-1

# Checkov configuration
CHECKOV_SKIP_CHECKS=CKV_AWS_1,CKV_AWS_2
```

## Advanced Usage

### Custom Plugin Configuration

```bash
# Configure Checkov to skip specific checks
export CHECKOV_SKIP_CHECKS=CKV_AWS_1,CKV_AWS_2
iac-scanner scan --directory /path/to/iac/code --tools checkov
```

### Disable LLM Processing

```bash
# Run without LLM processing
iac-scanner scan --directory /path/to/iac/code --disable-llm
```

### LLM Integration

The IAC Scanner can serve as a Master Control Program (MCP) that Large Language Models (LLMs) can interact with. This enables:

1. **Tool-Augmented LLM Capabilities**: LLMs can use the scanner as a tool to analyze IAC code and provide security recommendations.

2. **AI-Powered Security Analysis**: Combine the precision of static analysis tools with the reasoning capabilities of LLMs.

Example integration (see `examples/llm_integration` for full details):

```python
# Example of an LLM using the IAC Scanner API
import requests

# Query available plugins
plugins_response = requests.get("http://localhost:8000/plugins")
available_plugins = plugins_response.json()

# Scan IAC code
scan_response = requests.post(
    "http://localhost:8000/scan",
    json={
        "path": "/path/to/iac/code",
        "tools": ["zodiac", "checkov"]
    }
)
scan_results = scan_response.json()

# LLM would then process these results to generate recommendations
```

## Examples

See the `examples` directory for more detailed usage examples.

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## License

MIT 