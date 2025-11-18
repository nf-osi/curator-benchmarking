# OpenRouter Integration Guide

This document explains how to use OpenRouter API with the curator-benchmarking framework to test models like GPT-4, Gemini, and others not available in AWS Bedrock.

## What is OpenRouter?

[OpenRouter](https://openrouter.ai/) is a unified API that provides access to multiple AI models from different providers (OpenAI, Anthropic, Google, Meta, etc.) through a single interface. This allows you to test models like GPT-4, Gemini, and Llama without setting up separate accounts with each provider.

## Setup

### 1. Get an OpenRouter API Key

1. Visit https://openrouter.ai/
2. Sign up for an account
3. Go to https://openrouter.ai/keys to generate an API key
4. Note: OpenRouter charges per-token usage. Check their pricing at https://openrouter.ai/models for model costs.

### 2. Configure the API Key

**For Local Development:**

Option A - Environment Variable (recommended):
```bash
export OPENROUTER_API_KEY=your_api_key_here
```

Option B - Configuration File:
Create or edit `.aws/creds.yaml` in the repository root:
```yaml
OPENROUTER_API_KEY: your_api_key_here
```

**For GitHub Actions:**

1. Go to your repository settings
2. Navigate to Secrets and variables → Actions
3. Add a new secret named `OPENROUTER_API_KEY` with your API key as the value

The GitHub workflow is already configured to use this secret.

## Using OpenRouter Models

### Available Models

The framework includes popular OpenRouter models in the issue template dropdown:

**OpenAI Models:**
- `openai/gpt-4-turbo` - Latest GPT-4 Turbo
- `openai/gpt-4o` - GPT-4 Omni
- `openai/gpt-4o-mini` - Smaller, faster GPT-4
- `openai/o1-preview` - OpenAI o1 preview
- `openai/o1-mini` - Smaller o1 model

**Anthropic Models:**
- `anthropic/claude-3.5-sonnet` - Claude 3.5 Sonnet
- `anthropic/claude-3-opus` - Claude 3 Opus
- `anthropic/claude-3-sonnet` - Claude 3 Sonnet
- `anthropic/claude-3-haiku` - Claude 3 Haiku

**Google Models:**
- `google/gemini-pro-1.5` - Gemini Pro 1.5
- `google/gemini-flash-1.5` - Gemini Flash 1.5

**Meta Models:**
- `meta-llama/llama-3.3-70b-instruct` - Llama 3.3 70B

You can also use any other model listed on https://openrouter.ai/models by entering the model ID in the "Custom Model Endpoint" field.

### Via GitHub Issues

1. Create a new issue using the "Experiment Submission" template
2. Select an OpenRouter model from the dropdown (e.g., `openai/gpt-4-turbo`)
   - Or select "Other" and enter a custom model ID
3. Fill out the rest of the form as usual
4. Submit the issue

The experiment will automatically run using OpenRouter API.

**Example:**
```markdown
### Model Endpoint
openai/gpt-4-turbo

### Custom Model Endpoint
_No response_

### System Instructions
_No response_

### Temperature
0.0

### Thinking Mode
false

### Experiment Description
Testing GPT-4 Turbo on metadata curation tasks via OpenRouter
```

### Via Command Line

```bash
# Test with GPT-4 Turbo
python -m src.cli run correction_of_typos \
    --model openai/gpt-4-turbo \
    --temperature 0.0

# Test with Gemini Pro
python -m src.cli run column_enumeration \
    --model google/gemini-pro-1.5 \
    --temperature 0.1

# Test with Claude 3.5 Sonnet via OpenRouter
python -m src.cli run narrowing_of_broad_synonyms \
    --model anthropic/claude-3.5-sonnet \
    --system-instructions custom_instructions.txt
```

## Model ID Format

The framework automatically detects whether to use Bedrock or OpenRouter based on the model ID format:

**OpenRouter models** (routed to OpenRouter API):
- Format: `provider/model-name`
- Examples: `openai/gpt-4`, `anthropic/claude-3-opus`, `google/gemini-pro`

**Bedrock models** (routed to AWS Bedrock):
- Format: `prefix.model-id` or special prefixes
- Examples: `us.amazon.nova-premier-v1:0`, `global.anthropic.claude-sonnet-4-5-20250929-v1:0`

## Feature Support

OpenRouter models support most framework features:

- ✅ **System Instructions**: Fully supported
- ✅ **Temperature**: Fully supported
- ✅ **Tools**: Fully supported (MCP tools, ZOOMA, regex tester, etc.)
- ⚠️ **Thinking Mode**: Not supported (this is a Bedrock-specific feature)
- ✅ **Custom Prompts**: Fully supported
- ✅ **Multi-task Experiments**: Fully supported

## Cost Considerations

OpenRouter charges per token usage. Costs vary by model:
- GPT-4 models: ~$10-30 per 1M tokens
- Claude models: ~$3-15 per 1M tokens
- Gemini models: ~$1-5 per 1M tokens

Check current pricing at: https://openrouter.ai/models

A typical experiment across all 12 tasks with 10 samples each:
- Input: ~120K tokens
- Output: ~60K tokens
- Total cost: ~$0.50-5.00 depending on model

## Troubleshooting

### "OpenRouter API key not found" Error

**Cause**: The `OPENROUTER_API_KEY` environment variable or config file entry is not set.

**Solution**:
```bash
export OPENROUTER_API_KEY=your_key_here
```

Or add to `.aws/creds.yaml`:
```yaml
OPENROUTER_API_KEY: your_key_here
```

### Model Not Found Error

**Cause**: The model ID is incorrect or the model is not available on OpenRouter.

**Solution**: Check available models at https://openrouter.ai/models and use the correct model ID format (e.g., `openai/gpt-4-turbo`, not just `gpt-4-turbo`).

### Rate Limiting

**Cause**: You're making too many requests to OpenRouter API.

**Solution**: The framework automatically retries with exponential backoff. If you continue to hit rate limits, consider:
- Adding delays between experiments
- Using a model with higher rate limits
- Upgrading your OpenRouter plan

### Insufficient Credits

**Cause**: Your OpenRouter account doesn't have enough credits.

**Solution**: Add credits to your OpenRouter account at https://openrouter.ai/credits

## Comparing Models

You can easily compare Bedrock and OpenRouter models by running experiments with different model IDs:

```bash
# Run with Bedrock Claude
python -m src.cli run correction_of_typos \
    --model global.anthropic.claude-sonnet-4-5-20250929-v1:0

# Run with OpenRouter GPT-4
python -m src.cli run correction_of_typos \
    --model openai/gpt-4-turbo

# Run with OpenRouter Gemini
python -m src.cli run correction_of_typos \
    --model google/gemini-pro-1.5
```

Results will be saved separately and can be compared in the dashboard.

## Additional Resources

- OpenRouter Documentation: https://openrouter.ai/docs
- OpenRouter Models: https://openrouter.ai/models
- OpenRouter Pricing: https://openrouter.ai/models (see individual model pages)
- OpenRouter API Keys: https://openrouter.ai/keys
- Framework Documentation: [README.md](../README.md)
