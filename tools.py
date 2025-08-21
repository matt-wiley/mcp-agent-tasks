"""
MCP Tools for Task Management Server

This module defines all the MCP tools that will be registered with the server.
Each tool follows the MCP protocol for parameter validation and response formatting.
"""

from typing import Any, Dict
import logging
from mcp import Tool
from project_id import get_project_id as _get_project_id
from database import (
    get_work_items_for_project, 
    get_all_work_items_for_project,
    build_hierarchy,
    add_completion_summaries
)

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


async def get_current_work_plan(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP tool: Get the rolling work plan for a project (hides completed items)
    
    Args:
        arguments: Dictionary containing:
            - project_id (str): Project identifier from get_project_id
    
    Returns:
        Dict containing the hierarchical work plan with completion summaries
    
    Raises:
        ValueError: If project_id is missing or invalid
    """
    try:
        # Extract and validate project_id parameter
        project_id = arguments.get("project_id")
        if not project_id:
            raise ValueError("project_id parameter is required")
        
        # Get incomplete work items (rolling work plan)
        incomplete_items = get_work_items_for_project(project_id)
        
        # Get all items for completion summaries
        all_items = get_all_work_items_for_project(project_id)
        
        # Build hierarchy from incomplete items
        hierarchy = build_hierarchy(incomplete_items)
        
        # Add completion summaries using all items
        hierarchy_with_summaries = add_completion_summaries(hierarchy, all_items)
        
        logger.info(f"Generated work plan for project {project_id}: {len(hierarchy_with_summaries['projects'])} projects, {len(incomplete_items)} incomplete items")
        
        # Format response according to MCP specification
        return {
            "content": [
                {
                    "type": "text", 
                    "text": f"Current work plan retrieved for project: {project_id}\n\n"
                           f"Projects: {len(hierarchy_with_summaries['projects'])}\n"
                           f"Incomplete items: {len(incomplete_items)}\n"
                           f"Orphaned items: {len(hierarchy_with_summaries['orphaned_items'])}"
                }
            ],
            "data": hierarchy_with_summaries
        }
        
    except Exception as e:
        logger.error(f"Error in get_current_work_plan tool: {e}")
        raise ValueError(f"Failed to retrieve work plan: {str(e)}")


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
    ),
    Tool(
        name="get_current_work_plan", 
        description="Get the current rolling work plan for a project (shows incomplete items with completion summaries)",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier from get_project_id tool"
                }
            },
            "required": ["project_id"]
        }
    )
]


# Tool handler mapping
TOOL_HANDLERS = {
    "get_project_id": get_project_id,
    "get_current_work_plan": get_current_work_plan
}


if __name__ == "__main__":
    # Test the MCP tool wrapper
    import asyncio
    
    async def test_tools():
        print("Testing MCP tool wrappers:")
        
        # Test get_project_id
        test_cases = [
            {"project_info": "https://github.com/matt-wiley/mcp-agent-tasks.git"},
            {"project_info": "/home/matt/project"},
        ]
        
        for test_case in test_cases:
            print(f"\nTesting get_project_id with: {test_case}")
            try:
                result = await get_project_id(test_case)
                print(f"Success: {result['data']}")
            except Exception as e:
                print(f"Error: {e}")
        
        # Test get_current_work_plan
        print(f"\nTesting get_current_work_plan:")
        try:
            # Use a test project ID
            test_project_id = "dGVzdF9wcm9qZWN0"  # base64 for "test_project"
            result = await get_current_work_plan({"project_id": test_project_id})
            print(f"Success: {len(result['data']['projects'])} projects found")
        except Exception as e:
            print(f"Expected error (empty database): {e}")
        
        # Test error cases
        print(f"\nTesting error cases:")
        try:
            result = await get_project_id({})
            print(f"Unexpected success: {result}")
        except Exception as e:
            print(f"Expected error: {e}")
            
        try:
            result = await get_current_work_plan({})
            print(f"Unexpected success: {result}")
        except Exception as e:
            print(f"Expected error: {e}")
    
    asyncio.run(test_tools())
