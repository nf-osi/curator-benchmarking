"""Scoring and evaluation for experiment results."""
from typing import Dict, Any, Optional
import json


class Scorer:
    """Handles scoring of predictions against ground truth."""
    
    def score(
        self,
        prediction: str,
        ground_truth: Dict[str, Any]
    ) -> Optional[float]:
        """
        Score a prediction against ground truth using strict matching.
        
        Args:
            prediction: The model's prediction (must be valid JSON)
            ground_truth: The expected result as a dictionary
            
        Returns:
            Score between 0.0 and 1.0, or None if scoring is not possible
        """
        try:
            # Try to parse prediction as JSON
            try:
                pred_dict = json.loads(prediction)
            except (json.JSONDecodeError, TypeError):
                # If not JSON, return 0.0 - adherence to prompt format is part of the test
                return 0.0
            
            # If both are dictionaries, do strict structured comparison
            return self._structured_score(pred_dict, ground_truth)
        
        except Exception as e:
            print(f"Error scoring prediction: {e}")
            return None
    
    def _structured_score(
        self,
        prediction: Dict[str, Any],
        ground_truth: Dict[str, Any]
    ) -> float:
        """
        Score structured data (dictionaries) using strict exact matching.
        
        Adherence to the prompt (exact values, correct format) is part of the test.
        """
        if not isinstance(prediction, dict) or not isinstance(ground_truth, dict):
            return 0.0
        
        # Calculate field-level accuracy with strict matching
        all_keys = set(prediction.keys()) | set(ground_truth.keys())
        if not all_keys:
            return 1.0  # Both empty, perfect match
        
        matches = 0
        for key in all_keys:
            pred_val = prediction.get(key)
            truth_val = ground_truth.get(key)
            
            # Strict exact match only - no fuzzy matching
            if pred_val == truth_val:
                matches += 1
        
        return matches / len(all_keys)
    

