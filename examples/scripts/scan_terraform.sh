#!/bin/bash

# Change to the project root directory
cd "$(dirname "$0")/../.."

# Make sure the scanner is installed
pip install -e .

# Set up environment variables (can also be placed in .env file)
export AWS_REGION=us-east-1
export BEDROCK_MODEL_ID=anthropic.claude-v2

# Run the scan on the sample Terraform code with both Zodiac and Checkov
echo "Scanning Terraform code with multiple tools..."
iac-scanner scan \
  --path examples/terraform/simple-aws \
  --tools zodiac checkov \
  --output scan_results.json

echo "Scan complete. Results saved to scan_results.json"

# Print the list of available plugins
echo -e "\nAvailable plugins:"
iac-scanner plugins 