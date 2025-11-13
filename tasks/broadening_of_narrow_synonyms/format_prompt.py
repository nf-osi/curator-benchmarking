"""Custom prompt formatter for broadening_of_narrow_synonyms task."""
import json
from typing import Dict, Any, Optional


def format_prompt(
    prompt_template: str,
    sample: Dict[str, Any],
    ground_truth: Optional[Dict[str, Any]] = None,
    schema: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format the prompt for broadening_of_narrow_synonyms task.
    
    Args:
        prompt_template: The base prompt template from default_prompt.txt
        sample: Input sample data
        ground_truth: Ground truth sample (not used for formatting)
        schema: Optional JSON schema to include in the prompt
        
    Returns:
        Formatted prompt string
    """
    # Include schema if available
    schema_text = ""
    if schema and 'properties' in schema:
        schema_properties = schema['properties']
        if schema_properties:
            simplified_schema = {
                "type": "object",
                "properties": {}
            }
            for prop_name, prop_def in schema_properties.items():
                simplified_schema["properties"][prop_name] = {
                    "description": prop_def.get("description", ""),
                    "type": prop_def.get("type", "string")
                }
                if "enum" in prop_def:
                    simplified_schema["properties"][prop_name]["enum"] = prop_def["enum"]
            
            schema_text = f"\n\nTarget Schema (controlled terminology - use these exact values where enums are specified):\n{json.dumps(simplified_schema, indent=2)}"
    
    # Format prompt with sample data and schema
    sample_str = json.dumps(sample, indent=2)
    return f"{prompt_template}{schema_text}\n\nInput data:\n{sample_str}"

