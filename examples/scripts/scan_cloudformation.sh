#!/bin/bash

# Change to the project root directory
cd "$(dirname "$0")/../.."

# Make sure the scanner is installed
pip install -e .

# Set up environment variables (can also be placed in .env file)
export AWS_REGION=us-east-1
export BEDROCK_MODEL_ID=anthropic.claude-v2

# Run the scan on the sample CloudFormation template with both Zodiac and Checkov
echo "Scanning CloudFormation template with multiple tools..."
iac-scanner scan \
  --path examples/cloudformation/simple-aws \
  --tools zodiac checkov \
  --output cf_scan_results.json

echo "Scan complete. Results saved to cf_scan_results.json" 