# IAC Scanner Examples

This directory contains example code and scripts to demonstrate how to use the IAC Scanner.

## Directory Structure

- **terraform/** - Sample Terraform code
  - **simple-aws/** - A simple AWS infrastructure defined with Terraform
- **cloudformation/** - Sample CloudFormation templates
  - **simple-aws/** - A simple AWS infrastructure defined with CloudFormation
- **scripts/** - Example scripts to run IAC Scanner

## Security Issues in Example Code

The example IAC code intentionally contains several common security issues to demonstrate the scanner's capabilities:

1. Open SSH access (port 22) to the world (0.0.0.0/0)
2. Unencrypted S3 buckets
3. Unencrypted EBS volumes
4. Missing resource tagging

## Available Plugins

The IAC Scanner comes with the following plugins:

1. **Zodiac** - A tool for unearthing semantic checks for cloud Infrastructure-as-Code programs
2. **Checkov** - A static code analysis tool for infrastructure-as-code that detects security and compliance misconfigurations

## Running the Examples

### Prerequisites

Before running the examples, make sure you have:

1. Installed the IAC Scanner package: `pip install -e .` from the repository root
2. Set up AWS credentials if you plan to use the AWS Bedrock integration for LLM analysis
3. Cloned or configured access to the Zodiac repository for the Zodiac plugin
4. Installed Checkov (should be installed automatically as a dependency)

### Using the Shell Scripts

The `scripts` directory contains shell scripts to run the IAC Scanner:

```bash
# Scan Terraform code with both Zodiac and Checkov
./examples/scripts/scan_terraform.sh

# Scan CloudFormation template with both Zodiac and Checkov
./examples/scripts/scan_cloudformation.sh
```

### Using the Python Script

The `scripts` directory also contains a Python script that demonstrates how to use the IAC Scanner programmatically:

```bash
# Run the Python example
./examples/scripts/scan_iac.py
```

The Python script shows more advanced usage examples, including:
- Running scans with multiple plugins
- Configuring plugin-specific settings
- Processing results with or without the LLM

### Environment Variables

The scripts use the following environment variables:

- `AWS_REGION` - AWS region for Bedrock (default: "us-east-1")
- `BEDROCK_MODEL_ID` - Bedrock model ID (default: "anthropic.claude-v2")
- `AWS_PROFILE` - AWS profile name (optional)
- `AWS_ACCESS_KEY_ID` - AWS access key (optional)
- `AWS_SECRET_ACCESS_KEY` - AWS secret key (optional)

You can set these variables in your environment or in a `.env` file at the repository root.

## Expected Output

The scripts will generate JSON files containing scan results. Here's what to expect:

1. A list of detected security issues in the IAC code
2. Recommendations for fixing the issues
3. Prioritized issues from most critical to least critical

If LLM integration is enabled (via AWS Bedrock), the results will also include:
- A summary of findings
- Additional security concerns that might not be explicitly captured by the scanning tools

### Comparing Scan Results

You might notice differences between the results from Zodiac and Checkov:

- **Zodiac** focuses on unearthing semantic checks, examining relationships between resources and finding potential inconsistencies based on cloud provider constraints.
- **Checkov** focuses on security best practices and compliance standards, with a comprehensive set of pre-defined rules.

Together, these tools provide a more complete view of potential issues in your infrastructure code. 