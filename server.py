#!/usr/bin/env python3
"""
MCP Task Management Server

A Model Context Protocol (MCP) server that provides AI agents with task management
capabilities while achieving massive token savings through a "rolling work plan" approach.
"""

import logging
import asyncio
import json
from typing import Any, Dict, List

# MCP server imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import our database and tools modules
from database import init_database
from tools import (
    get_project_id,
    get_current_work_plan,
    create_work_item,
    update_work_item,
    complete_item,
    search_items
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("mcp-agent-tasks")

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List all available MCP tools."""
    return [
        Tool(
            name="get_project_id",
            description="Generate a consistent project ID from project information (git remote URL or absolute path)",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_info": {
                        "type": "string",
                        "description": "The project information - either a git remote URL or absolute path"
                    }
                },
                "required": ["project_info"]
            }
        ),
        Tool(
            name="get_current_work_plan",
            description="Get the current work plan for a project showing only incomplete items (rolling work plan)",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The project ID to get the work plan for"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="create_work_item",
            description="Create a new work item (project, phase, task, or subtask) in the hierarchical structure",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The project ID this work item belongs to"
                    },
                    "type": {
                        "type": "string",
                        "enum": ["project", "phase", "task", "subtask"],
                        "description": "The type of work item to create"
                    },
                    "title": {
                        "type": "string",
                        "description": "The title/name of the work item"
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional detailed description of the work item"
                    },
                    "parent_id": {
                        "type": "integer",
                        "description": "Optional parent item ID for hierarchy (required for non-project items)"
                    }
                },
                "required": ["project_id", "type", "title"]
            }
        ),
        Tool(
            name="update_work_item",
            description="Update an existing work item with new field values",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "The ID of the work item to update"
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
                    "order_index": {
                        "type": "number",
                        "description": "New ordering position for the work item"
                    }
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="complete_item",
            description="Mark a work item as completed",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "The ID of the work item to complete"
                    }
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="search_items",
            description="Search for work items within a project by text query",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The project ID to search within"
                    },
                    "query": {
                        "type": "string",
                        "description": "Text to search for in item titles and descriptions"
                    }
                },
                "required": ["project_id", "query"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls by routing to appropriate functions."""
    try:
        logger.info(f"Tool called: {name} with arguments: {arguments}")
        
        # Route to appropriate tool function
        if name == "get_project_id":
            result = await get_project_id(arguments)
        elif name == "get_current_work_plan":
            result = await get_current_work_plan(arguments)
        elif name == "create_work_item":
            result = await create_work_item(arguments)
        elif name == "update_work_item":
            result = await update_work_item(arguments)
        elif name == "complete_item":
            result = await complete_item(arguments)
        elif name == "search_items":
            result = await search_items(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        # Return the result content
        return result.get("content", [])
        
    except Exception as e:
        logger.error(f"Error in tool call {name}: {str(e)}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": f"Tool execution failed: {str(e)}",
                "tool": name,
                "arguments": arguments
            }, indent=2)
        )]

async def main():
    """Main server entry point."""
    logger.info("Starting MCP Task Management Server...")
    
    # Initialize database on startup
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # Start the server
    try:
        logger.info("Server ready and listening for connections...")
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        logger.info("Server shutting down...")

if __name__ == "__main__":
    asyncio.run(main())
