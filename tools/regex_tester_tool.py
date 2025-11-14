"""Tool for testing and validating regex patterns."""
import re
from typing import Dict, Any, List, Optional


def execute(
    regex_pattern: str,
    test_strings: List[str],
    expected_matches: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Test a regex pattern against a list of test strings.
    
    Args:
        regex_pattern: The regex pattern to test
        test_strings: List of strings to test the pattern against
        expected_matches: Optional list of expected matches (for validation)
        
    Returns:
        Dictionary containing test results
    """
    results = {
        "regex_pattern": regex_pattern,
        "test_results": [],
        "all_passed": True,
        "total_tests": len(test_strings)
    }
    
    try:
        # Compile the regex pattern
        compiled_pattern = re.compile(regex_pattern)
        
        for i, test_string in enumerate(test_strings):
            matches = compiled_pattern.findall(test_string)
            
            # Convert matches to strings if they're tuples (from groups)
            if matches:
                matches = [str(m) if not isinstance(m, tuple) else str(m[0]) if m[0] else "" for m in matches]
            
            test_result = {
                "test_string": test_string,
                "matches": matches,
                "matched": len(matches) > 0,
                "match_count": len(matches)
            }
            
            # If expected matches provided, validate
            if expected_matches and i < len(expected_matches):
                expected = expected_matches[i]
                test_result["expected"] = expected
                test_result["correct"] = matches == [expected] if isinstance(expected, str) else matches == expected
                if not test_result["correct"]:
                    results["all_passed"] = False
            
            results["test_results"].append(test_result)
        
        # Overall statistics
        matched_count = sum(1 for r in results["test_results"] if r["matched"])
        results["matched_count"] = matched_count
        results["match_rate"] = matched_count / len(test_strings) if test_strings else 0
        
        if expected_matches:
            correct_count = sum(1 for r in results["test_results"] if r.get("correct", False))
            results["correct_count"] = correct_count
            results["accuracy"] = correct_count / len(test_strings) if test_strings else 0
        
    except re.error as e:
        results["error"] = f"Invalid regex pattern: {str(e)}"
        results["all_passed"] = False
    except Exception as e:
        results["error"] = f"Error testing regex: {str(e)}"
        results["all_passed"] = False
    
    return results


def execute_validation(
    regex_pattern: str,
    test_strings: List[str],
    expected_matches: List[str]
) -> Dict[str, Any]:
    """
    Validate a regex pattern against expected matches.
    
    Args:
        regex_pattern: The regex pattern to validate
        test_strings: List of strings to test
        expected_matches: List of expected matches (one per test string)
        
    Returns:
        Dictionary containing validation results
    """
    return execute(regex_pattern, test_strings, expected_matches)

