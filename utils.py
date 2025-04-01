"""Utility functions for the OLAS MCP application."""
import re
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from models import Tool, ExecutionStep

def parse_apy(text: str) -> Optional[float]:
    """Extract APY percentage from text."""
    # Look for percentage patterns like 4.5% or 4,5%
    apy_matches = re.findall(r'(\d+[.,]?\d*)%', text)
    if apy_matches:
        try:
            # Convert the first match to a float, replacing comma with period
            return float(apy_matches[0].replace(',', '.'))
        except ValueError:
            return None
    return None

def infer_tools(prompt: str, available_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Infer which tools should be used based on the prompt.
    This is a simple keyword-based inference.
    
    Args:
        prompt: The user's prompt
        available_tools: List of available tools
        
    Returns:
        List of tool dictionaries to be used
    """
    prompt = prompt.lower()
    selected_tools = []
    
    tool_keywords = {
        "defillama": ["defillama", "defi", "tvl", "lending rate", "apy", "interest rate"],
        "thegraph": ["graph", "historical", "history", "protocol", "data", "metrics"],
        "spaceandtime": ["space", "time", "risk", "analysis", "quantitative", "assessment"],
        "chainlink": ["price", "oracle", "feed", "token", "valuation"]
    }
    
    for tool in available_tools:
        tool_name = tool.get("name", "").lower()
        # Skip tools that aren't available
        if not tool.get("available", True):
            continue
            
        # Check for direct mention of the tool
        if tool_name in prompt:
            selected_tools.append(tool)
            continue
            
        # Check for keywords associated with the tool
        for keyword_prefix, keywords in tool_keywords.items():
            if keyword_prefix in tool_name:
                if any(keyword in prompt for keyword in keywords):
                    selected_tools.append(tool)
                    break
    
    # If no tools were matched, select the first available tool as a fallback
    if not selected_tools:
        for tool in available_tools:
            if tool.get("available", True):
                selected_tools.append(tool)
                break
    
    return selected_tools

def create_execution_steps(selected_tools: List[Tool]) -> List[Dict[str, Any]]:
    """
    Create execution steps based on selected tools.
    
    Args:
        selected_tools: List of Tool objects
        
    Returns:
        List of execution step dictionaries
    """
    steps = []
    
    # Create a step for each tool
    for i, tool in enumerate(selected_tools):
        steps.append({
            "step": f"Step {i+1}: {tool.name}",
            "tool": tool.name,
            "status": "pending",
            "timestamp": datetime.now().isoformat()
        })
    
    # Add a final step for combining results if multiple tools
    if len(selected_tools) > 1:
        steps.append({
            "step": f"Final Step: Combine Results",
            "tool": "Aggregator",
            "status": "pending",
            "timestamp": datetime.now().isoformat()
        })
    
    return steps