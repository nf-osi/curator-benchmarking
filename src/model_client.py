"""Unified model client that routes to appropriate backend (Bedrock or OpenRouter)."""
from typing import Dict, Any, Optional, List
from .config import Config
from .bedrock_client import BedrockClient
from .openrouter_client import OpenRouterClient
from .tool import Tool
from .tool_executor import ToolExecutor


class ModelClient:
    """Unified client that routes to appropriate backend based on model ID."""
    
    def __init__(self, config: Config):
        """Initialize model client with configuration."""
        self.config = config
        self.bedrock_client = None
        self.openrouter_client = None
    
    def _is_openrouter_model(self, model_id: str) -> bool:
        """
        Determine if a model ID is for OpenRouter.
        
        OpenRouter model IDs typically follow the format:
        - openai/gpt-4
        - anthropic/claude-3-opus
        - google/gemini-pro
        
        Args:
            model_id: The model identifier
            
        Returns:
            True if this is an OpenRouter model
        """
        # OpenRouter models contain a slash in the ID
        # and don't start with specific Bedrock prefixes
        if '/' in model_id:
            # Exclude Bedrock models which also can have slashes
            bedrock_prefixes = (
                'us.', 'global.', 'anthropic.', 'amazon.',
                'deepseek.', 'meta.', 'openai.'
            )
            if not model_id.startswith(bedrock_prefixes):
                return True
        
        return False
    
    def _get_bedrock_client(self) -> BedrockClient:
        """Get or create Bedrock client."""
        if self.bedrock_client is None:
            self.bedrock_client = BedrockClient(self.config)
        return self.bedrock_client
    
    def _get_openrouter_client(self) -> OpenRouterClient:
        """Get or create OpenRouter client."""
        if self.openrouter_client is None:
            self.openrouter_client = OpenRouterClient(self.config)
        return self.openrouter_client
    
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
        Invoke a model with the given parameters.
        
        Automatically routes to Bedrock or OpenRouter based on model_id.
        
        Args:
            model_id: The model endpoint identifier
            prompt: The user prompt
            system_instructions: Optional system instructions (uses default if None)
            temperature: Sampling temperature
            thinking: Enable thinking mode (only supported on some models)
            max_tokens: Maximum tokens to generate
            max_retries: Number of retry attempts
            tools: Optional list of Tool objects to make available to the model
            tool_executor: Optional ToolExecutor for handling tool calls (required if tools provided)
            
        Returns:
            Dictionary containing the response and metadata
        """
        if self._is_openrouter_model(model_id):
            print(f"    [INFO] Using OpenRouter API for model: {model_id}")
            client = self._get_openrouter_client()
        else:
            print(f"    [INFO] Using AWS Bedrock for model: {model_id}")
            client = self._get_bedrock_client()
        
        return client.invoke_model(
            model_id=model_id,
            prompt=prompt,
            system_instructions=system_instructions,
            temperature=temperature,
            thinking=thinking,
            max_tokens=max_tokens,
            max_retries=max_retries,
            tools=tools,
            tool_executor=tool_executor
        )
