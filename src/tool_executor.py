"""Tool execution handler for LLM tool calls."""
import json
from typing import Dict, Any, List, Optional
from .tool import Tool, ToolRegistry


class ToolExecutor:
    """
    Handles execution of tool calls requested by the LLM.
    
    When the LLM requests a tool call, this executor:
    1. Finds the appropriate tool
    2. Executes it with the provided parameters
    3. Returns the result in a format the LLM can use
    """
    
    def __init__(self, tool_registry: ToolRegistry):
        """
        Initialize tool executor.
        
        Args:
            tool_registry: Registry containing available tools
        """
        self.tool_registry = tool_registry
        self.execution_history: List[Dict[str, Any]] = []
    
    def execute_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single tool call from the LLM.
        
        Args:
            tool_call: Tool call request from the LLM, containing:
                - toolUseId: Unique ID for this tool call
                - name: Name of the tool to call
                - input: Parameters for the tool
                
        Returns:
            Dictionary containing:
                - toolUseId: The ID from the request
                - status: 'success' or 'error'
                - content: Result content (list of text blocks for Bedrock format)
        """
        tool_name = tool_call.get('name')
        tool_use_id = tool_call.get('toolUseId')
        parameters = tool_call.get('input', {})
        
        if not tool_name:
            return {
                "toolUseId": tool_use_id or "unknown",
                "status": "error",
                "content": [{"text": "Tool name missing from tool call"}]
            }
        
        tool = self.tool_registry.get(tool_name)
        if not tool:
            error_msg = f"Tool '{tool_name}' not found in registry"
            self.execution_history.append({
                "tool_name": tool_name,
                "tool_use_id": tool_use_id,
                "status": "error",
                "error": error_msg
            })
            return {
                "toolUseId": tool_use_id or "unknown",
                "status": "error",
                "content": [{"text": error_msg}]
            }
        
        try:
            # Execute the tool
            result = tool.execute(parameters)
            
            # Serialize result to JSON string for Bedrock
            if isinstance(result, (dict, list)):
                result_text = json.dumps(result, indent=2)
            else:
                result_text = str(result)
            
            # Record successful execution
            self.execution_history.append({
                "tool_name": tool_name,
                "tool_use_id": tool_use_id,
                "parameters": parameters,
                "status": "success",
                "result": result
            })
            
            return {
                "toolUseId": tool_use_id or "unknown",
                "status": "success",
                "content": [{"text": result_text}]
            }
        except Exception as e:
            error_msg = f"Error executing tool '{tool_name}': {str(e)}"
            self.execution_history.append({
                "tool_name": tool_name,
                "tool_use_id": tool_use_id,
                "parameters": parameters,
                "status": "error",
                "error": error_msg
            })
            return {
                "toolUseId": tool_use_id or "unknown",
                "status": "error",
                "content": [{"text": error_msg}]
            }
    
    def execute_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute multiple tool calls.
        
        Args:
            tool_calls: List of tool call requests
            
        Returns:
            List of tool results in Bedrock format
        """
        results = []
        for tool_call in tool_calls:
            result = self.execute_tool_call(tool_call)
            results.append(result)
        return results
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """
        Get history of all tool executions.
        
        Returns:
            List of execution records
        """
        return self.execution_history.copy()
    
    def clear_history(self):
        """Clear execution history."""
        self.execution_history.clear()

