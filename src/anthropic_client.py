"""Direct Anthropic API client for models not available via Bedrock or OpenRouter.

Used for bare first-party model IDs like "claude-fable-5". Claude Fable 5 is
not available on Bedrock without 30-day data retention and is not offered on
OpenRouter, so it must be called through the Anthropic API directly.
"""
import time
from typing import Dict, Any, Optional, List

import anthropic

from .config import Config
from .tool import Tool
from .tool_executor import ToolExecutor
from .bedrock_client import _rejects_sampling_params


class AnthropicClient:
    """Client for the first-party Anthropic API."""

    def __init__(self, config: Config):
        self.config = config
        api_key = config.get_anthropic_api_key()
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Set the environment variable or add "
                "ANTHROPIC_API_KEY to .aws/creds.yaml (in CI, add a repository "
                "secret named ANTHROPIC_API_KEY)."
            )
        self.client = anthropic.Anthropic(api_key=api_key)

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
        """Invoke an Anthropic API model. Tools are not supported on this path."""
        if tools:
            return {
                'success': False,
                'error': 'Tools are not supported for direct Anthropic API models yet',
                'model_id': model_id,
            }

        if system_instructions is None:
            system_instructions = self.config.default_system_instructions

        kwargs = {
            'model': model_id,
            'max_tokens': max_tokens,
            'messages': [{'role': 'user', 'content': prompt}],
        }
        if system_instructions:
            kwargs['system'] = system_instructions
        # Claude Fable 5 / Opus 5 / Sonnet 5 / Opus 4.7+ reject sampling params.
        # Fable 5 also rejects any explicit thinking config (thinking is always
        # on), so we never send a thinking parameter here; on those models the
        # experiment's thinking flag has no effect (reasoning is model-default).
        if not _rejects_sampling_params(model_id):
            kwargs['temperature'] = temperature

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.messages.create(**kwargs)

                if response.stop_reason == 'refusal':
                    # Do not fall back to another model: this is a benchmark, a
                    # refusal is a failed sample for the model under test.
                    details = getattr(response, 'stop_details', None)
                    category = getattr(details, 'category', None) if details else None
                    return {
                        'success': False,
                        'error': f"Model refused (category: {category})",
                        'model_id': model_id,
                        'attempt': attempt,
                    }

                content = ''.join(
                    block.text for block in response.content if block.type == 'text'
                )
                usage = response.usage
                return {
                    'success': True,
                    'content': content,
                    'model_id': model_id,
                    'usage': {
                        'inputTokens': usage.input_tokens,
                        'outputTokens': usage.output_tokens,
                        'totalTokens': usage.input_tokens + usage.output_tokens,
                    },
                    'attempt': attempt,
                }
            except anthropic.BadRequestError as e:
                # Not retryable: surface immediately
                return {
                    'success': False,
                    'error': f"Bad request: {e.message}",
                    'model_id': model_id,
                    'attempt': attempt,
                }
            except (anthropic.RateLimitError, anthropic.APIStatusError,
                    anthropic.APIConnectionError) as e:
                last_error = e
                if attempt < max_retries:
                    delay = min(2 ** attempt, 30)
                    print(f"    [WARN] Anthropic API error (attempt {attempt}/{max_retries}), "
                          f"retrying in {delay}s: {e}")
                    time.sleep(delay)

        return {
            'success': False,
            'error': f"Max retries exceeded: {last_error}",
            'model_id': model_id,
        }
