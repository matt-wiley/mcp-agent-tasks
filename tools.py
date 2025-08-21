"""
MCP Tools for Task Management Server

This module defines all the MCP tools that will be registered with the server.
Each tool follows the MCP protocol for parameter validation and response formatting.
"""

from typing import Any, Dict
import logging
from mcp import Tool
from project_id import get_project_id as _get_project_id

logger = logging.getLogger(__name__)


async def get_project_id(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP tool: Generate consistent project ID from project information
    
    Args:
        arguments: Dictionary containing:
            - project_info (str): Git remote URL or absolute project path
    
    Returns:
        Dict containing project_id and raw_value
    
    Raises:
        ValueError: If project_info is missing or invalid
    """
    try:
        # Extract and validate project_info parameter
        project_info = arguments.get("project_info")
        if not project_info:
            raise ValueError("project_info parameter is required")
        
        # Call the pure function
        result = _get_project_id(project_info)
        
        logger.info(f"Generated project ID for: {project_info[:50]}{'...' if len(project_info) > 50 else ''}")
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Project ID generated successfully.\n\nProject ID: {result['project_id']}\nRaw Value: {result['raw_value']}"
                }
            ],
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error in get_project_id tool: {e}")
        raise ValueError(f"Failed to generate project ID: {str(e)}")


# Tool definitions for MCP server registration
TOOLS = [
    Tool(
        name="get_project_id",
        description="Generate a consistent project ID from project information (Git remote URL or absolute path)",
        inputSchema={
            "type": "object",
            "properties": {
                "project_info": {
                    "type": "string",
                    "description": "Git remote URL (preferred) or absolute path to project root"
                }
            },
            "required": ["project_info"]
        }
    )
]


# Tool handler mapping
TOOL_HANDLERS = {
    "get_project_id": get_project_id
}


if __name__ == "__main__":
    # Test the MCP tool wrapper
    import asyncio
    
    async def test_tools():
        print("Testing MCP tool wrappers:")
        
        test_cases = [
            {"project_info": "https://github.com/matt-wiley/mcp-agent-tasks.git"},
            {"project_info": "/home/matt/project"},
        ]
        
        for test_case in test_cases:
            print(f"\nTesting with: {test_case}")
            try:
                result = await get_project_id(test_case)
                print(f"Success: {result['data']}")
            except Exception as e:
                print(f"Error: {e}")
        
        # Test error case
        print(f"\nTesting error case:")
        try:
            result = await get_project_id({})
            print(f"Unexpected success: {result}")
        except Exception as e:
            print(f"Expected error: {e}")
    
    asyncio.run(test_tools())
