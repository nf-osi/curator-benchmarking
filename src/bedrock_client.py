"""AWS Bedrock client for running LLM inference."""
import json
import time
import boto3
import requests
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError
from .config import Config


class BedrockClient:
    """Client for interacting with AWS Bedrock."""
    
    def __init__(self, config: Config):
        """Initialize Bedrock client with configuration."""
        self.config = config
        self.bearer_token = config.get_bearer_token()
        
        # If bearer token is available, we'll use direct HTTP requests
        # Otherwise, use boto3 with AWS credentials
        if not self.bearer_token:
            # Build client kwargs - use credentials from env if available, otherwise use default chain
            client_kwargs = {'region_name': config.aws_region}
            
            aws_key = config.get_aws_access_key()
            aws_secret = config.get_aws_secret_key()
            
            if aws_key and aws_secret:
                client_kwargs['aws_access_key_id'] = aws_key
                client_kwargs['aws_secret_access_key'] = aws_secret
            
            self.bedrock_runtime = boto3.client('bedrock-runtime', **client_kwargs)
            self.use_bearer_token = False
        else:
            # Use bearer token for authentication
            self.use_bearer_token = True
            self.bedrock_runtime = None
            # Construct the Bedrock endpoint URL
            # Note: Some models may use different endpoints or require different URL formats
            self.bedrock_endpoint = f"https://bedrock-runtime.{config.aws_region}.amazonaws.com"
    
    def invoke_model(
        self,
        model_id: str,
        prompt: str,
        system_instructions: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Invoke a Bedrock model with the given parameters.
        
        Args:
            model_id: The model endpoint identifier
            prompt: The user prompt
            system_instructions: Optional system instructions (uses default if None)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            max_retries: Number of retry attempts
            
        Returns:
            Dictionary containing the response and metadata
        """
        if system_instructions is None:
            system_instructions = self.config.default_system_instructions
        
        # Prepare the request body for Claude models
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        if system_instructions:
            body["system"] = system_instructions
        
        for attempt in range(max_retries):
            try:
                if self.use_bearer_token:
                    # Use bearer token authentication with direct HTTP request
                    # Try /foundation-model/{model_id}/invoke endpoint first
                    url = f"{self.bedrock_endpoint}/foundation-model/{model_id}/invoke"
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {self.bearer_token}'
                    }
                    
                    try:
                        response = requests.post(url, headers=headers, json=body, timeout=300)
                        response.raise_for_status()
                        response_body = response.json()
                        
                        # Check if we got an UnknownOperationException
                        if 'Output' in response_body and isinstance(response_body.get('Output'), dict):
                            error_type = response_body['Output'].get('__type', '')
                            if 'UnknownOperationException' in error_type:
                                # Fall back to boto3 if bearer token doesn't work for this model
                                raise ValueError("UnknownOperationException - falling back to boto3")
                    except (requests.exceptions.HTTPError, ValueError) as e:
                        # Fall back to boto3 if bearer token fails
                        # Initialize boto3 client if not already done
                        if not hasattr(self, '_boto3_client'):
                            client_kwargs = {'region_name': self.config.aws_region}
                            aws_key = self.config.get_aws_access_key()
                            aws_secret = self.config.get_aws_secret_key()
                            if aws_key and aws_secret:
                                client_kwargs['aws_access_key_id'] = aws_key
                                client_kwargs['aws_secret_access_key'] = aws_secret
                            self._boto3_client = boto3.client('bedrock-runtime', **client_kwargs)
                        
                        # Use boto3 instead
                        response = self._boto3_client.invoke_model(
                            modelId=model_id,
                            body=json.dumps(body)
                        )
                        response_body = json.loads(response['body'].read())
                else:
                    # Use boto3 with AWS credentials
                    response = self.bedrock_runtime.invoke_model(
                        modelId=model_id,
                        body=json.dumps(body)
                    )
                    response_body = json.loads(response['body'].read())
                
                # Extract content based on model response format
                content = ''
                
                # Try Anthropic format first (content array with text)
                if 'content' in response_body:
                    content_list = response_body.get('content', [])
                    if content_list and isinstance(content_list, list):
                        content = content_list[0].get('text', '')
                
                # Try OpenAI format (choices array)
                if not content and 'choices' in response_body:
                    choices = response_body.get('choices', [])
                    if choices and isinstance(choices, list):
                        choice = choices[0]
                        if 'message' in choice:
                            content = choice['message'].get('content', '')
                        elif 'text' in choice:
                            content = choice.get('text', '')
                
                # Fallback: try direct text field
                if not content:
                    content = response_body.get('text', response_body.get('output', ''))
                
                return {
                    'success': True,
                    'content': content,
                    'model_id': model_id,
                    'usage': response_body.get('usage', {}),
                    'attempt': attempt + 1,
                    'raw_response': response_body  # Include for debugging
                }
            
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                if error_code == 'ThrottlingException' and attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    time.sleep(wait_time)
                    continue
                else:
                    return {
                        'success': False,
                        'error': str(e),
                        'error_code': error_code,
                        'model_id': model_id,
                        'attempt': attempt + 1
                    }
            
            except requests.exceptions.HTTPError as e:
                # Handle HTTP errors from bearer token requests
                error_code = None
                error_message = str(e)
                try:
                    error_body = e.response.json()
                    error_code = error_body.get('__type', '')
                    error_message = error_body.get('message', error_body.get('error', str(e)))
                    # Include full error details for debugging
                    print(f"    [ERROR] HTTP {e.response.status_code}: {error_message}")
                    if error_body:
                        print(f"    [ERROR] Full error response: {error_body}")
                except:
                    pass
                
                if 'Throttling' in str(e) or '429' in str(e.response.status_code):
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        time.sleep(wait_time)
                        continue
                
                return {
                    'success': False,
                    'error': error_message,
                    'error_code': error_code or f'HTTP_{e.response.status_code}',
                    'model_id': model_id,
                    'attempt': attempt + 1
                }
            
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'model_id': model_id,
                    'attempt': attempt + 1
                }
        
        return {
            'success': False,
            'error': 'Max retries exceeded',
            'model_id': model_id
        }

