"""Tool for validating data against JSON schemas."""
import json
from typing import Dict, Any, Optional
from pathlib import Path


def execute(
    data: Dict[str, Any],
    schema_path: str,
    strict: bool = False
) -> Dict[str, Any]:
    """
    Validate data against a JSON schema.
    
    Args:
        data: The data dictionary to validate
        schema_path: Path to the JSON schema file
        strict: If True, return detailed error information
        
    Returns:
        Dictionary containing validation results
    """
    try:
        # Load schema
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        # Try to use jsonschema library if available
        try:
            import jsonschema
            from jsonschema import validate, ValidationError
            
            try:
                validate(instance=data, schema=schema)
                return {
                    "valid": True,
                    "data": data,
                    "schema_path": schema_path,
                    "errors": []
                }
            except ValidationError as e:
                errors = [{
                    "message": e.message,
                    "path": list(e.path),
                    "validator": e.validator,
                    "validator_value": e.validator_value
                }]
                
                if strict:
                    errors.append({
                        "absolute_path": list(e.absolute_path),
                        "absolute_schema_path": list(e.absolute_schema_path),
                        "context": [str(c) for c in e.context]
                    })
                
                return {
                    "valid": False,
                    "data": data,
                    "schema_path": schema_path,
                    "errors": errors,
                    "error_message": str(e)
                }
        
        except ImportError:
            # Fallback: basic validation without jsonschema
            return _basic_validation(data, schema, schema_path)
    
    except FileNotFoundError:
        return {
            "error": f"Schema file not found: {schema_path}",
            "valid": False
        }
    except json.JSONDecodeError as e:
        return {
            "error": f"Invalid JSON in schema file: {str(e)}",
            "valid": False
        }
    except Exception as e:
        return {
            "error": f"Error validating data: {str(e)}",
            "valid": False
        }


def _basic_validation(data: Dict[str, Any], schema: Dict[str, Any], schema_path: str) -> Dict[str, Any]:
    """Basic validation without jsonschema library."""
    errors = []
    
    # Check required fields
    required = schema.get("required", [])
    for field in required:
        if field not in data:
            errors.append({
                "message": f"Required field '{field}' is missing",
                "path": [field],
                "validator": "required"
            })
    
    # Check properties
    properties = schema.get("properties", {})
    for field_name, field_value in data.items():
        if field_name in properties:
            prop_def = properties[field_name]
            
            # Check type
            expected_type = prop_def.get("type")
            if expected_type:
                actual_type = type(field_value).__name__
                type_map = {
                    "string": "str",
                    "integer": "int",
                    "number": ("int", "float"),
                    "boolean": "bool",
                    "array": "list",
                    "object": "dict"
                }
                
                expected_python_type = type_map.get(expected_type)
                if isinstance(expected_python_type, tuple):
                    if actual_type not in expected_python_type:
                        errors.append({
                            "message": f"Field '{field_name}' has wrong type: expected {expected_type}, got {actual_type}",
                            "path": [field_name],
                            "validator": "type"
                        })
                elif actual_type != expected_python_type:
                    errors.append({
                        "message": f"Field '{field_name}' has wrong type: expected {expected_type}, got {actual_type}",
                        "path": [field_name],
                        "validator": "type"
                    })
            
            # Check enum
            if "enum" in prop_def:
                if field_value not in prop_def["enum"]:
                    errors.append({
                        "message": f"Field '{field_name}' value '{field_value}' is not in allowed enum values",
                        "path": [field_name],
                        "validator": "enum",
                        "allowed_values": prop_def["enum"]
                    })
    
    return {
        "valid": len(errors) == 0,
        "data": data,
        "schema_path": schema_path,
        "errors": errors
    }


def execute_field_validation(
    field_name: str,
    field_value: Any,
    schema_path: str
) -> Dict[str, Any]:
    """
    Validate a single field against a schema.
    
    Args:
        field_name: Name of the field to validate
        field_value: Value to validate
        schema_path: Path to the JSON schema file
        
    Returns:
        Dictionary containing validation results for the field
    """
    try:
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        properties = schema.get("properties", {})
        if field_name not in properties:
            return {
                "valid": False,
                "field_name": field_name,
                "error": f"Field '{field_name}' not found in schema"
            }
        
        prop_def = properties[field_name]
        errors = []
        
        # Check type
        expected_type = prop_def.get("type")
        if expected_type:
            actual_type = type(field_value).__name__
            type_map = {
                "string": "str",
                "integer": "int",
                "number": ("int", "float"),
                "boolean": "bool"
            }
            expected_python_type = type_map.get(expected_type)
            if isinstance(expected_python_type, tuple):
                if actual_type not in expected_python_type:
                    errors.append(f"Wrong type: expected {expected_type}, got {actual_type}")
            elif actual_type != expected_python_type:
                errors.append(f"Wrong type: expected {expected_type}, got {actual_type}")
        
        # Check enum
        if "enum" in prop_def:
            if field_value not in prop_def["enum"]:
                errors.append(f"Value '{field_value}' not in allowed enum values: {prop_def['enum']}")
        
        return {
            "valid": len(errors) == 0,
            "field_name": field_name,
            "field_value": field_value,
            "errors": errors,
            "allowed_values": prop_def.get("enum")
        }
    
    except Exception as e:
        return {
            "valid": False,
            "field_name": field_name,
            "error": str(e)
        }

