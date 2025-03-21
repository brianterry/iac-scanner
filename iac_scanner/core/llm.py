"""LLM client for enhancing IAC scanning with AWS Bedrock models."""

import json
import logging
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError


class LLMClient:
    """Client for interacting with AWS Bedrock models to enhance IAC scanning."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the LLM client.
        
        Args:
            config: Configuration dictionary. Supported keys:
                - aws_region: AWS region for Bedrock (default: "us-east-1")
                - model_id: Bedrock model ID (default: "anthropic.claude-v2")
                - temperature: Temperature for generation (default: 0.2)
                - max_tokens: Maximum tokens for generation (default: 4000)
                - aws_profile: AWS profile name (optional)
                - aws_access_key: AWS access key (optional)
                - aws_secret_key: AWS secret key (optional)
        """
        self.config = config or {}
        self.logger = logging.getLogger("iac_scanner.llm")
        self._bedrock_client = None
        
        # Initialize the AWS Bedrock client
        self._initialize_bedrock_client()
    
    def _initialize_bedrock_client(self):
        """Initialize the AWS Bedrock client."""
        try:
            session_kwargs = {}
            
            # Check if profile or access keys are provided
            if self.config.get("aws_profile"):
                session_kwargs["profile_name"] = self.config.get("aws_profile")
            elif self.config.get("aws_access_key") and self.config.get("aws_secret_key"):
                session_kwargs["aws_access_key_id"] = self.config.get("aws_access_key")
                session_kwargs["aws_secret_access_key"] = self.config.get("aws_secret_key")
            
            # Create a session with the provided credentials
            session = boto3.Session(**session_kwargs)
            
            # Create a Bedrock client
            self._bedrock_client = session.client(
                service_name="bedrock-runtime",
                region_name=self.config.get("aws_region", "us-east-1")
            )
            
            self.logger.info("AWS Bedrock client initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing AWS Bedrock client: {e}")
            self._bedrock_client = None
    
    def is_available(self) -> bool:
        """Check if the LLM service is available.
        
        Returns:
            True if the LLM is available, False otherwise
        """
        return self._bedrock_client is not None
    
    async def process_scan_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Process scan results with the LLM.
        
        Args:
            results: Scan results to process
            
        Returns:
            Processed scan results with additional insights
        """
        if not self.is_available():
            return results
        
        try:
            # Get the model ID from config
            model_id = self.config.get("model_id", "anthropic.claude-v2")
            
            # Format the prompt based on the model
            if "anthropic" in model_id:
                prompt = self._create_anthropic_prompt(results)
                request_body = {
                    "prompt": prompt,
                    "max_tokens_to_sample": self.config.get("max_tokens", 4000),
                    "temperature": self.config.get("temperature", 0.2),
                    "top_p": 0.9,
                }
            elif "amazon" in model_id:
                prompt = self._create_amazon_prompt(results)
                request_body = {
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": self.config.get("max_tokens", 4000),
                        "temperature": self.config.get("temperature", 0.2),
                        "topP": 0.9,
                    }
                }
            else:
                # Default to a generic prompt format
                prompt = self._create_generic_prompt(results)
                request_body = {
                    "prompt": prompt,
                    "max_tokens": self.config.get("max_tokens", 4000),
                    "temperature": self.config.get("temperature", 0.2),
                }
            
            # Invoke the model
            response = self._bedrock_client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )
            
            # Parse the response based on the model
            body = json.loads(response.get("body").read())
            
            if "anthropic" in model_id:
                llm_result = body.get("completion", "")
            elif "amazon" in model_id:
                llm_result = body.get("results", [{}])[0].get("outputText", "")
            else:
                llm_result = body.get("generated_text", "")
            
            # Parse the JSON response
            try:
                processed_results = json.loads(llm_result)
            except json.JSONDecodeError:
                # If not valid JSON, attempt to extract JSON from the text
                try:
                    # Look for JSON between curly braces
                    start_idx = llm_result.find('{')
                    end_idx = llm_result.rfind('}') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = llm_result[start_idx:end_idx]
                        processed_results = json.loads(json_str)
                    else:
                        raise ValueError("No JSON found in response")
                except (ValueError, json.JSONDecodeError):
                    # If still not valid, return a formatted error
                    self.logger.error("Failed to parse LLM response as JSON")
                    return {
                        "raw_results": results,
                        "error": "Failed to parse LLM response as JSON",
                        "llm_response": llm_result
                    }
            
            # Add the original results
            processed_results["raw_results"] = results
            
            return processed_results
        except ClientError as e:
            self.logger.error(f"AWS Bedrock error: {e}")
            return {
                "raw_results": results,
                "error": f"AWS Bedrock error: {str(e)}"
            }
        except Exception as e:
            self.logger.error(f"Error processing scan results with LLM: {e}")
            return {
                "raw_results": results,
                "error": str(e)
            }
    
    def _create_anthropic_prompt(self, results: Dict[str, Any]) -> str:
        """Create a prompt for Anthropic Claude models.
        
        Args:
            results: Scan results to analyze
            
        Returns:
            Formatted prompt for Claude
        """
        system_content = (
            "You are an expert in cloud Infrastructure as Code (IaC) and security. "
            "Your task is to analyze scan results from different IaC scanning tools "
            "and provide insights, recommendations, and a prioritized list of issues."
        )
        
        human_content = (
            f"I have the following scan results from Infrastructure as Code scanning tools:\n\n"
            f"{json.dumps(results, indent=2)}\n\n"
            f"Please analyze these results and provide:\n"
            f"1. A summary of the findings\n"
            f"2. Prioritized issues from most critical to least critical\n"
            f"3. Recommendations to fix the issues\n"
            f"4. Additional security concerns that might not be captured by the tools\n\n"
            f"Format your response as JSON with the keys: 'summary', 'prioritized_issues', "
            f"'recommendations', and 'additional_concerns'."
        )
        
        return f"\n\nHuman: {system_content}\n\n{human_content}\n\nAssistant:"
    
    def _create_amazon_prompt(self, results: Dict[str, Any]) -> str:
        """Create a prompt for Amazon Titan models.
        
        Args:
            results: Scan results to analyze
            
        Returns:
            Formatted prompt for Titan
        """
        return (
            f"You are an expert in cloud Infrastructure as Code (IaC) and security. "
            f"Analyze the following scan results from IaC scanning tools:\n\n"
            f"{json.dumps(results, indent=2)}\n\n"
            f"Provide: 1) Summary of findings 2) Prioritized issues from most to least critical "
            f"3) Recommendations to fix issues 4) Additional security concerns.\n\n"
            f"Format response as JSON with keys: 'summary', 'prioritized_issues', "
            f"'recommendations', and 'additional_concerns'."
        )
    
    def _create_generic_prompt(self, results: Dict[str, Any]) -> str:
        """Create a generic prompt for other models.
        
        Args:
            results: Scan results to analyze
            
        Returns:
            Formatted generic prompt
        """
        return (
            f"Analyze these Infrastructure as Code scan results as a security expert:\n\n"
            f"{json.dumps(results, indent=2)}\n\n"
            f"Return a JSON with keys: 'summary', 'prioritized_issues', 'recommendations', "
            f"and 'additional_concerns'."
        ) 