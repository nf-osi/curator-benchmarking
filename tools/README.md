# Tools for LLM Experiments

This directory contains tools that can be used by LLMs during experiments. Tools are resources that the LLM can leverage to improve performance on tasks.

## Tool Configuration Format

Tools are defined in JSON or YAML configuration files. The configuration format is:

```json
{
  "tools": [
    {
      "type": "function",
      "name": "tool_name",
      "description": "Description of what the tool does",
      "schema": {
        "type": "object",
        "properties": {
          "param1": {
            "type": "string",
            "description": "Description of parameter"
          }
        },
        "required": ["param1"]
      },
      "function_path": "path/to/tool.py",
      "function_name": "execute"
    }
  ]
}
```

## Tool Types

### Function Tools

Function tools execute Python functions. They require:
- `type`: "function"
- `name`: Unique tool identifier
- `description`: What the tool does
- `schema`: OpenAPI schema defining parameters
- `function_path`: Path to Python file containing the function
- `function_name`: Name of the function to call (default: "execute")

The function should accept keyword arguments matching the schema properties and return a JSON-serializable result.

### API Tools

API tools make HTTP requests to external APIs. They require:
- `type`: "api"
- `name`: Unique tool identifier
- `description`: What the tool does
- `schema`: OpenAPI schema defining parameters
- `api_url`: The API endpoint URL
- `api_method`: HTTP method (GET, POST, etc.)

## Using Tools in Experiments

To use tools in an experiment, provide a tools configuration file:

```bash
# Use OLS MCP tool
python -m src.cli run --tools tools/ols_tools.json

# Or use the example configuration
python -m src.cli run --tools tools/example_tools.json
```

The experiment will:
1. Load tools from the configuration file
2. Make them available to the LLM during inference
3. Track which tools were used in each sample
4. Include tool usage information in results

## Tool Execution Flow

1. LLM receives prompt with available tools
2. LLM may request tool calls if needed
3. Tool executor runs the requested tools
4. Tool results are returned to the LLM
5. LLM generates final response using tool results

## OLS MCP Tool

The OLS (Ontology Lookup Service) MCP tool provides access to the OLS MCP API for ontology term lookup, mapping, and cross-product retrieval.

### Operations

- **search**: Search for ontology terms by label
- **mappings**: Get mappings for a specific term in an ontology
- **cross_product**: Get cross-product mappings for an ontology
- **term**: Get detailed information about a term by IRI

### Example Usage

```python
# Search for terms
ols_mcp(operation="search", term="diabetes", ontology="doid")

# Get mappings for a term
ols_mcp(operation="mappings", term="diabetes", ontology="doid")

# Get term by IRI
ols_mcp(operation="term", iri="http://purl.obolibrary.org/obo/DOID_1612", ontology="doid")
```

### Configuration Files

- `ols_tools.json`: OLS MCP tool configuration
- `example_tools.json`: Example configuration (uses OLS MCP tool)
- `ols_mcp_tool.py`: OLS MCP tool implementation

## Creating Custom Tools

To create a custom tool:

1. Create a Python file with an `execute` function:

```python
def execute(param1: str, param2: int) -> dict:
    # Tool logic here
    return {"result": "..."}
```

2. Define the tool schema in a configuration file
3. Reference the tool in your experiment

## Tool Performance Tracking

Tool usage is tracked in experiment results:
- `tool_calls`: List of tool calls made by the LLM
- `tool_execution_history`: Detailed execution history
- Tool names are included in experiment metadata

This allows you to compare performance with and without tools to measure their impact.

