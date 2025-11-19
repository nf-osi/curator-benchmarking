"""OpenRouter client for running LLM inference via OpenRouter API."""
import json
import time
import requests
from typing import Dict, Any, Optional, List
from .config import Config
from .tool import Tool
from .tool_executor import ToolExecutor


class OpenRouterClient:
    """Client for interacting with OpenRouter API."""
    
    def __init__(self, config: Config):
        """Initialize OpenRouter client with configuration."""
        self.config = config
        self.api_key = config.get_openrouter_api_key()
        self.base_url = "https://openrouter.ai/api/v1"
        
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key not found. Please set OPENROUTER_API_KEY environment variable "
                "or add it to .aws/creds.yaml"
            )
    
    def _convert_tools_to_openrouter_format(self, tools: List[Tool]) -> List[Dict[str, Any]]:
        """
        Convert Tool objects to OpenRouter API format (OpenAI-compatible).
        
        Args:
            tools: List of Tool objects
            
        Returns:
            List of tool definitions in OpenAI format
        """
        result = []
        for tool in tools:
            schema = tool.get_schema()
            result.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": schema
                }
            })
        return result
    
    def _extract_tool_calls_from_response(self, response_body: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract tool calls from an OpenRouter response."""
        tool_calls = []
        
        if 'choices' in response_body:
            for choice in response_body.get('choices', []):
                message = choice.get('message', {})
                if 'tool_calls' in message:
                    for tool_call in message['tool_calls']:
                        # Parse arguments if it's a string
                        arguments = tool_call.get('function', {}).get('arguments', '{}')
                        if isinstance(arguments, str):
                            try:
                                arguments = json.loads(arguments)
                            except:
                                arguments = {}
                        
                        tool_calls.append({
                            'toolUseId': tool_call.get('id') or f"call_{len(tool_calls)}",
                            'name': tool_call.get('function', {}).get('name'),
                            'input': arguments
                        })
        
        return tool_calls
    
    def _invoke_model_with_tools(
        self,
        model_id: str,
        prompt: str,
        system_instructions: str,
        temperature: float,
        max_tokens: int,
        max_retries: int,
        tools: List[Tool],
        tool_executor: ToolExecutor
    ) -> Dict[str, Any]:
        """
        Invoke model with tools, handling tool use flow.
        
        This method handles the multi-turn conversation where the model may request
        tool calls, we execute them, and continue the conversation.
        """
        # Convert tools to OpenRouter format
        openrouter_tools = self._convert_tools_to_openrouter_format(tools)
        
        # Build initial messages
        messages = []
        if system_instructions:
            messages.append({
                "role": "system",
                "content": system_instructions
            })
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Maximum tool use iterations to prevent infinite loops
        max_tool_iterations = 10
        tool_iterations = 0
        all_tool_calls = []
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        for attempt in range(max_retries):
            try:
                while tool_iterations < max_tool_iterations:
                    # Build API call parameters
                    body = {
                        "model": model_id,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "tools": openrouter_tools
                    }
                    
                    response = requests.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=body,
                        timeout=300
                    )
                    response.raise_for_status()
                    response_body = response.json()
                    
                    # Check for tool calls
                    tool_calls = self._extract_tool_calls_from_response(response_body)
                    
                    if not tool_calls:
                        # No tool calls - we have the final response
                        break
                    
                    # Execute tool calls
                    tool_results = tool_executor.execute_tool_calls(tool_calls)
                    all_tool_calls.extend(tool_calls)
                    
                    # Add assistant message with tool calls
                    assistant_message = {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": []
                    }
                    
                    # Add tool calls to assistant message
                    if 'choices' in response_body and len(response_body['choices']) > 0:
                        choice = response_body['choices'][0]
                        if 'message' in choice and 'tool_calls' in choice['message']:
                            assistant_message['tool_calls'] = choice['message']['tool_calls']
                    
                    messages.append(assistant_message)
                    
                    # Add tool results as tool messages
                    for result in tool_results:
                        tool_use_id = result.get('toolUseId')
                        
                        # Extract result content
                        result_content = ""
                        for content_item in result.get('content', []):
                            if isinstance(content_item, dict):
                                result_content += content_item.get('text', '')
                            elif isinstance(content_item, str):
                                result_content += content_item
                        
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_use_id,
                            "content": result_content
                        })
                    
                    tool_iterations += 1
                
                # Extract final content
                content = ''
                if 'choices' in response_body and len(response_body['choices']) > 0:
                    choice = response_body['choices'][0]
                    message = choice.get('message', {})
                    if 'content' in message and message['content']:
                        content = message['content']
                
                # Extract usage information
                usage = response_body.get('usage', {})
                
                return {
                    'success': True,
                    'content': content,
                    'model_id': model_id,
                    'usage': {
                        'inputTokens': usage.get('prompt_tokens', 0),
                        'outputTokens': usage.get('completion_tokens', 0),
                        'totalTokens': usage.get('total_tokens', 0)
                    },
                    'attempt': attempt + 1,
                    'raw_response': response_body,
                    'tool_calls': all_tool_calls,
                    'tool_execution_history': tool_executor.get_execution_history()
                }
            
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                else:
                    return {
                        'success': False,
                        'error': str(e),
                        'error_code': f'HTTP_{e.response.status_code}',
                        'model_id': model_id,
                        'attempt': attempt + 1,
                        'tool_calls': all_tool_calls
                    }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'model_id': model_id,
                    'attempt': attempt + 1,
                    'tool_calls': all_tool_calls
                }
        
        return {
            'success': False,
            'error': 'Max retries exceeded',
            'model_id': model_id,
            'tool_calls': all_tool_calls
        }
    
    def invoke_model(
        self,
        model_id: str,
        prompt: str,
        system_instructions: Optional[str] = None,
        temperature: float = 0.0,
        thinking: bool = False,
        max_tokens: int = 4096,
        max_retries: int = 3,
        tools: Optional[List[Tool]] = None,
        tool_executor: Optional[ToolExecutor] = None
    ) -> Dict[str, Any]:
        """
        Invoke an OpenRouter model with the given parameters.
        
        Args:
            model_id: The model identifier (e.g., 'openai/gpt-4', 'anthropic/claude-3-opus')
            prompt: The user prompt
            system_instructions: Optional system instructions
            temperature: Sampling temperature
            thinking: Enable thinking mode (not supported by OpenRouter, ignored)
            max_tokens: Maximum tokens to generate
            max_retries: Number of retry attempts
            tools: Optional list of Tool objects to make available to the model
            tool_executor: Optional ToolExecutor for handling tool calls (required if tools provided)
            
        Returns:
            Dictionary containing the response and metadata
        """
        if system_instructions is None:
            system_instructions = self.config.default_system_instructions
        
        # If tools are provided, use tool-aware invocation
        if tools and tool_executor:
            return self._invoke_model_with_tools(
                model_id=model_id,
                prompt=prompt,
                system_instructions=system_instructions,
                temperature=temperature,
                max_tokens=max_tokens,
                max_retries=max_retries,
                tools=tools,
                tool_executor=tool_executor
            )
        
        # Standard invocation without tools
        messages = []
        if system_instructions:
            messages.append({
                "role": "system",
                "content": system_instructions
            })
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        body = {
            "model": model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=body,
                    timeout=300
                )
                response.raise_for_status()
                response_body = response.json()
                
                # Extract content
                content = ''
                if 'choices' in response_body and len(response_body['choices']) > 0:
                    choice = response_body['choices'][0]
                    message = choice.get('message', {})
                    if 'content' in message:
                        content = message['content']
                
                # Extract usage information
                usage = response_body.get('usage', {})
                
                return {
                    'success': True,
                    'content': content,
                    'model_id': model_id,
                    'usage': {
                        'inputTokens': usage.get('prompt_tokens', 0),
                        'outputTokens': usage.get('completion_tokens', 0),
                        'totalTokens': usage.get('total_tokens', 0)
                    },
                    'attempt': attempt + 1,
                    'raw_response': response_body
                }
            
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                else:
                    error_message = str(e)
                    try:
                        error_body = e.response.json()
                        error_message = error_body.get('error', {}).get('message', str(e))
                    except:
                        pass
                    
                    return {
                        'success': False,
                        'error': error_message,
                        'error_code': f'HTTP_{e.response.status_code}',
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
