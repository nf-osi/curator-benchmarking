"""Tool for fuzzy matching against controlled vocabularies."""
from typing import Dict, Any, List, Optional
from difflib import SequenceMatcher
import json


def _similarity(a: str, b: str) -> float:
    """Calculate similarity between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def execute(
    value: str,
    candidates: List[str],
    threshold: float = 0.6,
    max_results: int = 5
) -> Dict[str, Any]:
    """
    Find fuzzy matches for a value against a list of candidates.
    
    Args:
        value: The value to match
        candidates: List of candidate strings to match against
        threshold: Minimum similarity threshold (0.0 to 1.0)
        max_results: Maximum number of results to return
        
    Returns:
        Dictionary containing matches sorted by similarity
    """
    if not value or not candidates:
        return {
            "value": value,
            "matches": [],
            "found": False,
            "message": "Value or candidates list is empty"
        }
    
    # Calculate similarity for each candidate
    matches = []
    for candidate in candidates:
        similarity = _similarity(value, candidate)
        if similarity >= threshold:
            matches.append({
                "candidate": candidate,
                "similarity": round(similarity, 4),
                "exact_match": similarity == 1.0
            })
    
    # Sort by similarity (descending)
    matches.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Limit results
    matches = matches[:max_results]
    
    return {
        "value": value,
        "threshold": threshold,
        "matches": matches,
        "found": len(matches) > 0,
        "best_match": matches[0] if matches else None,
        "total_candidates": len(candidates)
    }


def execute_with_schema(
    value: str,
    schema_path: str,
    field_name: Optional[str] = None,
    threshold: float = 0.6,
    max_results: int = 5
) -> Dict[str, Any]:
    """
    Find fuzzy matches for a value against enum values in a JSON schema.
    
    Args:
        value: The value to match
        schema_path: Path to JSON schema file
        field_name: Optional field name to match against (if None, matches all enum fields)
        threshold: Minimum similarity threshold
        max_results: Maximum number of results to return
        
    Returns:
        Dictionary containing matches
    """
    try:
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        # Extract enum values from schema
        all_enums = []
        field_enums = {}
        
        properties = schema.get("properties", {})
        for prop_name, prop_def in properties.items():
            if "enum" in prop_def:
                enum_values = prop_def["enum"]
                field_enums[prop_name] = enum_values
                all_enums.extend(enum_values)
        
        # Determine which enums to search
        if field_name and field_name in field_enums:
            candidates = field_enums[field_name]
            search_field = field_name
        else:
            candidates = list(set(all_enums))  # Remove duplicates
            search_field = "all_fields"
        
        # Perform fuzzy match
        result = execute(value, candidates, threshold, max_results)
        result["schema_path"] = schema_path
        result["field_name"] = search_field
        
        return result
    
    except FileNotFoundError:
        return {
            "error": f"Schema file not found: {schema_path}",
            "value": value
        }
    except json.JSONDecodeError:
        return {
            "error": f"Invalid JSON in schema file: {schema_path}",
            "value": value
        }
    except Exception as e:
        return {
            "error": f"Error processing schema: {str(e)}",
            "value": value
        }

