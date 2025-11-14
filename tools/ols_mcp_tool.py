"""Tool for accessing the OLS (Ontology Lookup Service) MCP API."""
import requests
from typing import Dict, Any, Optional
from urllib.parse import quote


def execute(
    operation: str,
    term: Optional[str] = None,
    ontology: Optional[str] = None,
    iri: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Access the OLS MCP API to retrieve ontology mappings and cross-products.
    
    Args:
        operation: The operation to perform. Options:
            - "mappings": Get mappings for a term
            - "search": Search for ontology terms
            - "cross_product": Get cross-product mappings
            - "term": Get term information by IRI
        term: The term or label to search for
        ontology: The ontology ID (e.g., "go", "chebi", "efo")
        iri: The IRI of the term (for term lookup)
        **kwargs: Additional parameters for the API call
        
    Returns:
        Dictionary containing the API response
    """
    base_url = "https://www.ebi.ac.uk/ols4/api/mcp"
    
    try:
        if operation == "mappings":
            # Get mappings for a term
            if not term or not ontology:
                return {
                    "error": "Both 'term' and 'ontology' are required for mappings operation",
                    "operation": operation
                }
            
            # Search for the term first to get its IRI
            search_url = f"{base_url}/search"
            search_params = {
                "q": term,
                "ontology": ontology,
                "exact": "true",
                "size": 1
            }
            
            search_response = requests.get(search_url, params=search_params, timeout=10)
            search_response.raise_for_status()
            search_data = search_response.json()
            
            if not search_data.get("_embedded", {}).get("terms"):
                return {
                    "operation": operation,
                    "term": term,
                    "ontology": ontology,
                    "found": False,
                    "message": f"Term '{term}' not found in ontology '{ontology}'"
                }
            
            term_iri = search_data["_embedded"]["terms"][0]["iri"]
            
            # Get mappings for the term - URL encode the IRI
            encoded_iri = quote(term_iri, safe='')
            mappings_url = f"{base_url}/ontologies/{ontology}/terms/{encoded_iri}/mappings"
            mappings_response = requests.get(mappings_url, timeout=10)
            mappings_response.raise_for_status()
            mappings_data = mappings_response.json()
            
            return {
                "operation": operation,
                "term": term,
                "ontology": ontology,
                "iri": term_iri,
                "mappings": mappings_data.get("_embedded", {}).get("mappings", []),
                "found": True
            }
        
        elif operation == "search":
            # Search for ontology terms
            if not term:
                return {
                    "error": "'term' is required for search operation",
                    "operation": operation
                }
            
            search_url = f"{base_url}/search"
            search_params = {
                "q": term,
                "size": kwargs.get("size", 10)
            }
            
            if ontology:
                search_params["ontology"] = ontology
            
            if kwargs.get("exact"):
                search_params["exact"] = "true"
            
            response = requests.get(search_url, params=search_params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            terms = data.get("_embedded", {}).get("terms", [])
            
            return {
                "operation": operation,
                "term": term,
                "ontology": ontology,
                "results_count": data.get("page", {}).get("totalElements", 0),
                "terms": [
                    {
                        "label": t.get("label"),
                        "iri": t.get("iri"),
                        "ontology": t.get("ontology_name"),
                        "description": t.get("description", [])
                    }
                    for t in terms
                ],
                "found": len(terms) > 0
            }
        
        elif operation == "cross_product":
            # Get cross-product mappings
            if not ontology:
                return {
                    "error": "'ontology' is required for cross_product operation",
                    "operation": operation
                }
            
            cross_product_url = f"{base_url}/ontologies/{ontology}/cross-products"
            params = {}
            
            if kwargs.get("size"):
                params["size"] = kwargs["size"]
            
            response = requests.get(cross_product_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                "operation": operation,
                "ontology": ontology,
                "cross_products": data.get("_embedded", {}).get("crossProducts", []),
                "found": True
            }
        
        elif operation == "term":
            # Get term information by IRI
            if not iri or not ontology:
                return {
                    "error": "Both 'iri' and 'ontology' are required for term operation",
                    "operation": operation
                }
            
            # URL encode the IRI
            encoded_iri = quote(iri, safe='')
            term_url = f"{base_url}/ontologies/{ontology}/terms/{encoded_iri}"
            response = requests.get(term_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                "operation": operation,
                "iri": iri,
                "ontology": ontology,
                "term": data,
                "found": True
            }
        
        else:
            return {
                "error": f"Unknown operation: {operation}",
                "valid_operations": ["mappings", "search", "cross_product", "term"]
            }
    
    except requests.exceptions.RequestException as e:
        return {
            "error": f"API request failed: {str(e)}",
            "operation": operation
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "operation": operation
        }

