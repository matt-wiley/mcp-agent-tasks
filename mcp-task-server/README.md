# MCP Task Management Server

A minimal Model Context Protocol (MCP) server that enables AI agents to manage tasks without burning context tokens through a "rolling work plan" approach.

## Overview

This MCP server provides 6 core tools for task management:
- `get_project_id()` - Generate consistent project identifiers
- `get_current_work_plan()` - Retrieve rolling work plan (hides completed items)
- `create_work_item()` - Create new work items in hierarchy
- `update_work_item()` - Update existing work items
- `complete_item()` - Mark items as completed
- `search_items()` - Search work items within project scope

## Key Features

- **Token Efficient**: Single task operations use <100 tokens vs 1000+ for file-based approaches
- **Rolling Work Plan**: Completed items auto-hide, maintaining focus on current work
- **Project Scoped**: Each project gets isolated task management
- **Hierarchical**: Supports Project → Phase → Task → Subtask structure
- **Audit Trail**: All changes logged with timestamps

## Quick Start

### Prerequisites
- Python 3.8+ 
- MCP-compatible client (Claude Desktop, etc.)

### Installation

1. Clone and navigate to the server directory:
```bash
git clone https://github.com/matt-wiley/mcp-agent-tasks.git
cd mcp-agent-tasks/mcp-task-server
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the MCP server:
```bash
python server.py
```

### MCP Client Configuration

Add to your MCP client configuration:
```json
{
  "mcpServers": {
    "task-manager": {
      "command": "python",
      "args": ["/path/to/mcp-agent-tasks/mcp-task-server/server.py"],
      "cwd": "/path/to/mcp-agent-tasks/mcp-task-server"
    }
  }
}
```

## Usage Example

```
Agent: "Determine the current project context and create a project called 'Website Redesign' with a research phase containing a task called 'User interviews'."

1. Agent calls get_project_id("https://github.com/user/repo.git")
2. Agent calls create_work_item("project", "Website Redesign", "", null)
3. Agent calls create_work_item("phase", "Research Phase", "", project_id)  
4. Agent calls create_work_item("task", "User interviews", "", phase_id)
5. Agent calls get_current_work_plan(project_id) to show structure
```

## Database

Uses SQLite (`tasks.db`) with two main tables:
- `work_items` - Hierarchical task structure with project scoping
- `changelog` - Audit trail of all changes

Database is created automatically on first run.

## Token Efficiency

Typical token usage:
- Single task completion: ~50 tokens
- Current work plan retrieval: ~200-400 tokens  
- Task creation: ~75 tokens

Compare to file-based approaches requiring 1000+ tokens to load context.

## Project Structure

```
mcp-task-server/
├── server.py          # Main MCP server script
├── database.py        # SQLite operations  
├── tasks.db          # SQLite database (created on first run)
├── requirements.txt   # Python dependencies
└── README.md         # This file
```

## Troubleshooting

**Database Issues:**
- Ensure write permissions in server directory
- Delete `tasks.db` to reset (loses all data)

**MCP Connection Issues:**
- Verify Python path in MCP client config
- Check server starts without errors: `python server.py --test`

**Tool Discovery Issues:**
- Restart MCP client after server changes
- Verify all 6 tools appear in client tool list

## Development

To run tests:
```bash
python -m pytest tests/
```

To reset database:
```bash
rm tasks.db
python server.py  # Will recreate on startup
```

## License

See LICENSE file in repository root.
