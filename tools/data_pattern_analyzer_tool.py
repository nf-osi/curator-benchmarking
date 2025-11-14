"""Tool for analyzing data patterns to infer types and formats."""
import re
from typing import Dict, Any, List, Optional
from datetime import datetime


def execute(
    values: List[str],
    analyze_format: bool = True
) -> Dict[str, Any]:
    """
    Analyze a list of values to infer data type and patterns.
    
    Args:
        values: List of string values to analyze
        analyze_format: Whether to analyze specific formats (dates, emails, etc.)
        
    Returns:
        Dictionary containing type inference and pattern analysis
    """
    if not values:
        return {
            "error": "Empty values list",
            "inferred_type": "unknown"
        }
    
    # Type detection
    type_scores = {
        "string": 0,
        "integer": 0,
        "number": 0,
        "boolean": 0,
        "date": 0,
        "datetime": 0,
        "email": 0,
        "url": 0
    }
    
    format_patterns = []
    boolean_patterns = {
        "true": ["true", "yes", "1", "y"],
        "false": ["false", "no", "0", "n"]
    }
    
    for value in values:
        value_str = str(value).strip()
        
        # Boolean detection
        if value_str.lower() in boolean_patterns["true"]:
            type_scores["boolean"] += 1
        elif value_str.lower() in boolean_patterns["false"]:
            type_scores["boolean"] += 1
        
        # Integer detection
        elif re.match(r'^-?\d+$', value_str):
            type_scores["integer"] += 1
        
        # Number detection (float)
        elif re.match(r'^-?\d+\.\d+$', value_str):
            type_scores["number"] += 1
        
        # Date detection
        elif analyze_format:
            date_formats = [
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%m/%d/%Y",
                "%d/%m/%Y",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S"
            ]
            for fmt in date_formats:
                try:
                    datetime.strptime(value_str, fmt)
                    if "T" in fmt or "%H" in fmt:
                        type_scores["datetime"] += 1
                    else:
                        type_scores["date"] += 1
                    format_patterns.append(fmt)
                    break
                except ValueError:
                    continue
        
        # Email detection
        if analyze_format and re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value_str):
            type_scores["email"] += 1
        
        # URL detection
        if analyze_format and re.match(r'^https?://[^\s/$.?#].[^\s]*$', value_str):
            type_scores["url"] += 1
        
        # Default to string
        if not any(type_scores[t] > 0 for t in ["boolean", "integer", "number", "date", "datetime", "email", "url"]):
            type_scores["string"] += 1
    
    # Determine inferred type
    inferred_type = max(type_scores, key=type_scores.get)
    confidence = type_scores[inferred_type] / len(values) if values else 0
    
    # Get unique format patterns
    unique_formats = list(set(format_patterns))
    
    return {
        "values_analyzed": len(values),
        "inferred_type": inferred_type,
        "confidence": round(confidence, 4),
        "type_scores": {k: v for k, v in type_scores.items() if v > 0},
        "detected_formats": unique_formats if unique_formats else None,
        "sample_values": values[:5]  # Include first 5 values as samples
    }


def execute_column_analysis(
    column_name: str,
    values: List[str]
) -> Dict[str, Any]:
    """
    Analyze a column of data to infer its type.
    
    Args:
        column_name: Name of the column
        values: List of values in the column
        
    Returns:
        Dictionary containing column type analysis
    """
    analysis = execute(values, analyze_format=True)
    analysis["column_name"] = column_name
    return analysis

