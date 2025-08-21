"""
MCP Tools for Task Management Server

This module defines all the MCP tools that will be registered with the server.
Each tool follows the MCP protocol for parameter validation and response formatting.
"""

from typing import Any, Dict
import logging
import json
from mcp import Tool
from project_id import get_project_id as _get_project_id
from database import (
    get_work_items_for_project, 
    get_all_work_items_for_project,
    build_hierarchy,
    add_completion_summaries,
    create_work_item as _create_work_item,
    update_work_item as _update_work_item,
    complete_item as _complete_item,
    search_work_items_with_context as _search_work_items_with_context
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


async def create_work_item(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP tool: Create a new work item in the hierarchical structure
    
    Args:
        arguments: Dictionary containing:
            - project_id (str): Project identifier from get_project_id
            - type (str): Type of item (project, phase, task, subtask)
            - title (str): Title of the work item
            - description (str, optional): Description of the work item
            - parent_id (int, optional): Parent item ID for hierarchy
            - notes (str, optional): Additional notes
    
    Returns:
        Dict containing the created work item data
    
    Raises:
        ValueError: If required fields are missing or validation fails
    """
    try:
        # Extract and validate required parameters
        project_id = arguments.get("project_id")
        if not project_id:
            raise ValueError("project_id parameter is required")
        
        item_type = arguments.get("type")
        if not item_type:
            raise ValueError("type parameter is required")
        
        title = arguments.get("title")
        if not title:
            raise ValueError("title parameter is required")
        
        # Extract optional parameters
        description = arguments.get("description")
        parent_id = arguments.get("parent_id")
        notes = arguments.get("notes")
        
        # Create the work item (includes validation and changelog logging)
        created_item = _create_work_item(
            project_id=project_id,
            item_type=item_type,
            title=title,
            description=description,
            parent_id=parent_id,
            notes=notes
        )
        
        logger.info(f"Created work item via MCP: {created_item['id']} - {item_type} '{title}'")
        
        # Format response according to MCP specification
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Work item created successfully!\n\n"
                           f"ID: {created_item['id']}\n"
                           f"Type: {created_item['type']}\n"
                           f"Title: {created_item['title']}\n"
                           f"Status: {created_item['status']}\n"
                           f"Project: {created_item['project_id']}"
                           + (f"\nParent ID: {created_item['parent_id']}" if created_item['parent_id'] else "")
                           + (f"\nDescription: {created_item['description']}" if created_item['description'] else "")
                }
            ],
            "data": created_item
        }
        
    except Exception as e:
        logger.error(f"Error in create_work_item tool: {e}")
        raise ValueError(f"Failed to create work item: {str(e)}")


async def update_work_item(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP tool: Update an existing work item with flexible field updates
    
    Args:
        arguments: Dictionary containing:
            - id (int): ID of the work item to update
            - project_id (str): Project identifier for validation
            - title (str, optional): New title for the work item
            - description (str, optional): New description
            - status (str, optional): New status (not_started, in_progress, completed)
            - type (str, optional): New type (project, phase, task, subtask)
            - parent_id (int, optional): New parent ID for hierarchy
            - order_index (float, optional): New order index for positioning
    
    Returns:
        Dict containing the updated work item data
    
    Raises:
        ValueError: If required fields are missing or validation fails
    """
    try:
        # Extract and validate required parameters
        item_id = arguments.get("id")
        if item_id is None:  # Allow id=0
            raise ValueError("id parameter is required")
        
        project_id = arguments.get("project_id")
        if not project_id:
            raise ValueError("project_id parameter is required")
        
        # Extract optional update parameters
        updates = {}
        for field in ['title', 'description', 'status', 'type', 'parent_id', 'order_index']:
            if field in arguments:
                updates[field] = arguments[field]
        
        if not updates:
            raise ValueError("At least one field must be provided for update")
        
        # Update the work item (includes validation and changelog logging)
        updated_item = _update_work_item(item_id, project_id, **updates)
        
        logger.info(f"Updated work item via MCP: {updated_item['id']} - updated fields: {list(updates.keys())}")
        
        # Format response according to MCP specification
        return {
            "content": [
                {
                    "type": "text", 
                    "text": f"Work item updated successfully!\n\n"
                           f"ID: {updated_item['id']}\n"
                           f"Type: {updated_item['type']}\n"
                           f"Title: {updated_item['title']}\n"
                           f"Status: {updated_item['status']}\n"
                           f"Project: {updated_item['project_id']}"
                           + (f"\nParent ID: {updated_item['parent_id']}" if updated_item['parent_id'] else "")
                           + (f"\nDescription: {updated_item['description']}" if updated_item['description'] else "")
                           + f"\n\nUpdated fields: {', '.join(updates.keys())}"
                }
            ],
            "data": updated_item
        }
        
    except Exception as e:
        logger.error(f"Error in update_work_item tool: {e}")
        raise ValueError(f"Failed to update work item: {str(e)}")


async def complete_item(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP tool: Mark a work item as completed
    
    Args:
        arguments: Dictionary containing:
            - id (int): ID of the work item to complete
            - project_id (str): Project identifier for validation
    
    Returns:
        Dict containing completion confirmation and updated item data
    
    Raises:
        ValueError: If required fields are missing or item doesn't exist
    """
    try:
        # Extract and validate required parameters
        item_id = arguments.get("id")
        if item_id is None:  # Allow id=0
            raise ValueError("id parameter is required")
        
        project_id = arguments.get("project_id")
        if not project_id:
            raise ValueError("project_id parameter is required")
        
        # Complete the work item (includes validation and changelog logging)
        completed_item = _complete_item(item_id, project_id)
        
        logger.info(f"Completed work item via MCP: {completed_item['id']} - {completed_item['title']}")
        
        # Format response according to MCP specification
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Work item completed successfully!\n\n"
                           f"ID: {completed_item['id']}\n"
                           f"Title: {completed_item['title']}\n"
                           f"Type: {completed_item['type']}\n"
                           f"Status: {completed_item['status']}\n"
                           f"Completed: {completed_item['updated_at']}\n"
                           f"Project: {completed_item['project_id']}"
                           + (f"\nParent ID: {completed_item['parent_id']}" if completed_item['parent_id'] else "")
                }
            ],
            "data": completed_item
        }
        
    except Exception as e:
        logger.error(f"Error in complete_item tool: {e}")
        raise ValueError(f"Failed to complete work item: {str(e)}")


async def search_items(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for work items by query string with full context.
    
    Returns matching work items with their parent breadcrumb paths for context.
    """
    query = arguments.get("query")
    project_id = arguments.get("project_id")
    
    if not query:
        raise ValueError("query parameter is required")
    if not project_id:
        raise ValueError("project_id parameter is required")
    
    try:
        search_results = _search_work_items_with_context(project_id, query)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(search_results, indent=2)
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error in search_items tool: {e}")
        raise ValueError(f"Failed to search work items: {str(e)}")


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
    ),
    Tool(
        name="create_work_item",
        description="Create a new work item in the hierarchical project structure",
        inputSchema={
            "type": "object", 
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier from get_project_id tool"
                },
                "type": {
                    "type": "string",
                    "enum": ["project", "phase", "task", "subtask"],
                    "description": "Type of work item to create"
                },
                "title": {
                    "type": "string",
                    "description": "Title/name of the work item"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of the work item"
                },
                "parent_id": {
                    "type": "integer", 
                    "description": "Optional parent item ID for hierarchy (leave empty for top-level projects)"
                },
                "notes": {
                    "type": "string",
                    "description": "Optional additional notes"
                }
            },
            "required": ["project_id", "type", "title"]
        }
    ),
    Tool(
        name="update_work_item",
        description="Update an existing work item with flexible field modifications",
        inputSchema={
            "type": "object",
            "properties": {
                "id": {
                    "type": "integer",
                    "description": "ID of the work item to update"
                },
                "project_id": {
                    "type": "string", 
                    "description": "Project identifier from get_project_id tool"
                },
                "title": {
                    "type": "string",
                    "description": "New title for the work item"
                },
                "description": {
                    "type": "string",
                    "description": "New description for the work item"
                },
                "status": {
                    "type": "string",
                    "enum": ["not_started", "in_progress", "completed"],
                    "description": "New status for the work item"
                },
                "type": {
                    "type": "string",
                    "enum": ["project", "phase", "task", "subtask"],
                    "description": "New type for the work item"
                },
                "parent_id": {
                    "type": "integer",
                    "description": "New parent item ID for hierarchy changes"
                },
                "order_index": {
                    "type": "number",
                    "description": "New order index for positioning"
                }
            },
            "required": ["id", "project_id"]
        }
    ),
    Tool(
        name="complete_item",
        description="Mark a work item as completed with automatic timestamp",
        inputSchema={
            "type": "object",
            "properties": {
                "id": {
                    "type": "integer",
                    "description": "ID of the work item to complete"
                },
                "project_id": {
                    "type": "string",
                    "description": "Project identifier from get_project_id tool"
                }
            },
            "required": ["id", "project_id"]
        }
    ),
    Tool(
        name="search_items",
        description="Search for work items by query string with parent context",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to match against work item titles and descriptions"
                },
                "project_id": {
                    "type": "string",
                    "description": "Project identifier from get_project_id tool"
                }
            },
            "required": ["query", "project_id"]
        }
    )
]


# Tool handler mapping
TOOL_HANDLERS = {
    "get_project_id": get_project_id,
    "get_current_work_plan": get_current_work_plan,
    "create_work_item": create_work_item,
    "update_work_item": update_work_item,
    "complete_item": complete_item,
    "search_items": search_items
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
        
        # Test create_work_item
        print(f"\nTesting create_work_item:")
        try:
            test_project_id = "dGVzdF9wcm9qZWN0"  # base64 for "test_project"
            
            # Create a project
            project_result = await create_work_item({
                "project_id": test_project_id,
                "type": "project",
                "title": "MCP Test Project",
                "description": "A project created via MCP tool"
            })
            print(f"Created project: ID {project_result['data']['id']}")
            
            # Create a phase under the project
            phase_result = await create_work_item({
                "project_id": test_project_id,
                "type": "phase", 
                "title": "MCP Test Phase",
                "parent_id": project_result['data']['id']
            })
            print(f"Created phase: ID {phase_result['data']['id']}")
            
        except Exception as e:
            print(f"create_work_item error: {e}")
        
        # Test error cases
        print(f"\nTesting error cases:")
        error_test_cases = [
            ({}, "Missing all required fields"),
            ({"project_id": "test"}, "Missing type and title"),
            ({"project_id": "test", "type": "invalid", "title": "test"}, "Invalid type"),
            ({"project_id": "test", "type": "phase", "title": "test"}, "Phase without parent"),
        ]
        
        for test_args, test_name in error_test_cases:
            try:
                if 'get_project_id' in test_name:
                    result = await get_project_id(test_args)
                    print(f"✗ {test_name} should have failed")
                elif 'get_current_work_plan' in test_name:
                    result = await get_current_work_plan(test_args)
                    print(f"✗ {test_name} should have failed")
                else:
                    result = await create_work_item(test_args)
                    print(f"✗ {test_name} should have failed")
            except ValueError as e:
                print(f"✓ {test_name}: {str(e)[:50]}...")
            except Exception as e:
                print(f"? {test_name} failed unexpectedly: {e}")
    
    asyncio.run(test_tools())
