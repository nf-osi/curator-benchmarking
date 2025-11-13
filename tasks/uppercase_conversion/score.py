"""Custom scorer for uppercase_conversion task."""
import json
import re
from typing import Dict, Any, Optional


def _extract_json(text: str) -> Optional[str]:
    """Extract JSON from text, handling markdown code blocks."""
    text = re.sub(r'```json\s*\n?', '', text)
    text = re.sub(r'```\s*\n?', '', text)
    text = text.strip()
    
    start = text.find('{')
    end = text.rfind('}')
    
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    
    return text


def score(
    prediction: str,
    ground_truth: Dict[str, Any],
    input_data: Optional[Dict[str, Any]] = None
) -> Optional[float]:
    """
    Score uppercase conversion by comparing JSON objects.
    
    The ground truth has a "result" field containing a JSON string,
    which needs to be parsed before comparison.
    """
    try:
        # Extract JSON from prediction (handles markdown code blocks)
        json_str = _extract_json(prediction)
        
        # Parse prediction JSON
        try:
            pred_dict = json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return 0.0
        
        # Get the result JSON string from ground truth
        result_str = ground_truth.get('result', '')
        if not result_str:
            return 0.0
        
        # Parse the JSON string from ground truth
        try:
            if isinstance(result_str, str):
                expected_dict = json.loads(result_str)
            else:
                expected_dict = result_str
        except (json.JSONDecodeError, TypeError):
            return 0.0
        
        # Compare the two dictionaries
        if not isinstance(pred_dict, dict) or not isinstance(expected_dict, dict):
            return 0.0
        
        # Strict exact match
        if pred_dict == expected_dict:
            return 1.0
        
        return 0.0
    except Exception as e:
        print(f"Error scoring uppercase conversion: {e}")
        return None

