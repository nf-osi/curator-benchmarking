"""Tool for accessing the ZOOMA API to map free-text annotations to ontology terms."""
import requests
from typing import Dict, Any, Optional, List
from urllib.parse import quote


def execute(
    property_value: str,
    property_type: Optional[str] = None,
    ontologies: Optional[List[str]] = None,
    required: Optional[List[str]] = None,
    preferred: Optional[List[str]] = None,
    filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Map a free-text annotation to ontology terms using ZOOMA API.
    
    ZOOMA (ZERO Order Ontology Mapping Application) maps free-text annotations
    to ontology terms, which is perfect for synonym mapping and terminology standardization.
    
    Args:
        property_value: The free-text value to map (e.g., "diabetes", "NF1")
        property_type: Optional property type (e.g., "disease", "cell type")
        ontologies: Optional list of ontology IDs to search (e.g., ["doid", "efo"])
        required: Optional list of required ontology IDs
        preferred: Optional list of preferred ontology IDs
        filter: Optional filter string
        
    Returns:
        Dictionary containing mapping results
    """
    base_url = "https://www.ebi.ac.uk/spot/zooma/v2/api"
    
    try:
        # Build query parameters
        params = {
            "propertyValue": property_value
        }
        
        if property_type:
            params["propertyType"] = property_type
        
        if ontologies:
            params["ontologies"] = ",".join(ontologies)
        
        if required:
            params["required"] = ",".join(required)
        
        if preferred:
            params["preferred"] = ",".join(preferred)
        
        if filter:
            params["filter"] = filter
        
        # Make API request
        response = requests.get(
            f"{base_url}/services/annotate",
            params=params,
            timeout=10,
            headers={"Accept": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        
        # Process results
        annotations = []
        for item in data:
            annotation = {
                "property_value": item.get("propertyValue"),
                "property_type": item.get("propertyType"),
                "confidence": item.get("confidence"),
                "semantic_tags": item.get("semanticTags", []),
                "annotated_property": item.get("annotatedProperty", {}),
                "derived_from": item.get("derivedFrom", {})
            }
            annotations.append(annotation)
        
        # Extract best match (highest confidence)
        best_match = None
        if annotations:
            sorted_annotations = sorted(
                annotations,
                key=lambda x: x.get("confidence", "LOW"),
                reverse=True
            )
            best_match = sorted_annotations[0]
        
        return {
            "property_value": property_value,
            "property_type": property_type,
            "annotations": annotations,
            "annotation_count": len(annotations),
            "best_match": best_match,
            "found": len(annotations) > 0
        }
    
    except requests.exceptions.RequestException as e:
        return {
            "error": f"API request failed: {str(e)}",
            "property_value": property_value
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "property_value": property_value
        }


def execute_batch(
    property_values: List[str],
    property_type: Optional[str] = None,
    ontologies: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Map multiple free-text annotations to ontology terms (batch operation).
    
    Args:
        property_values: List of free-text values to map
        property_type: Optional property type
        ontologies: Optional list of ontology IDs to search
        
    Returns:
        Dictionary containing mapping results for each value
    """
    results = {
        "property_values": property_values,
        "mappings": {},
        "total_mapped": 0
    }
    
    for value in property_values:
        mapping = execute(value, property_type, ontologies)
        results["mappings"][value] = mapping
        if mapping.get("found"):
            results["total_mapped"] += 1
    
    results["mapping_rate"] = results["total_mapped"] / len(property_values) if property_values else 0
    
    return results

