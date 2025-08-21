# MCP Task Management Server - AI Coding Instructions

## Project Overview
This is an **MCP (Model Context Protocol) server** for AI agent task management that eliminates context token waste through a "rolling work plan" approach. The core value proposition is **80%+ token reduction** compared to file-based task management by showing only incomplete items and hiding completed work.

## Architecture & Key Components

### Core Design Pattern: Project-Scoped Isolation
- **Project ID Generation**: `project_id.py` uses base64 encoding of git remote URL or absolute path for deterministic, consistent project identification
- **Database**: Single SQLite file (`tasks.db`) with hierarchical work items (project → phase → task → subtask) scoped by `project_id`
- **Rolling Work Plan**: Only incomplete items (`not_started`, `in_progress`) are shown; completed items become summaries ("✓ All tasks completed")

### File Structure & Responsibilities
- `database.py` - SQLite operations, hierarchy building, completion summaries
- `project_id.py` - Pure function for consistent project ID generation 
- `tools.py` - MCP tool implementations (6 tools total)
- `IMPLEMENTATION_PLAN.md` - Detailed subtask breakdown with structured workflow
- `pyproject.toml` - UV package manager configuration

## Development Workflow (Critical)

### Package Manager: UV (Not pip/poetry)
**Always use `uv` commands:**
```bash
uv run python script.py        # Run with project dependencies
uv run python -c "code"        # Inline Python with dependencies  
uv add package                 # Add new dependencies
uv sync                        # Sync from pyproject.toml
```

### Structured Subtask Approach (6-Step Process)
1. **Make the changes** - Implement specific subtask requirements
2. **Verify the work** - Test imports, run validation, check functionality  
3. **Update docs** - Update `IMPLEMENTATION_PLAN.md` progress tracking
4. **Wait for review** - Present work for human approval (**STOP HERE**)
5. **Commit once approved** - Meaningful commit messages (only after explicit approval)
6. **Wait for approval** - Get explicit go-ahead before moving to next subtask (**STOP HERE AGAIN**)

#### Critical: Two Approval Gates
- **After Step 4**: Human must approve the implementation before any commits
- **After Step 5**: Human must approve moving to the next subtask - never auto-progress
- **No assumptions**: Even if the next subtask seems obvious, wait for explicit direction

#### Commit Practices (Critical)

- Follow the prompt in `.github/prompts/commit.prompt.md` when creating commits

## Key Technical Patterns

### Database Operations
- **Connection Pattern**: Use `get_connection()` context manager from `database.py`
- **Hierarchy Validation**: 4-level depth max, circular reference prevention
- **Audit Trail**: Every action logs to `changelog` table with `project_id`
- **Order Management**: `order_index` REAL field for flexible item ordering

### MCP Tool Implementation
```python
# Standard MCP tool pattern in tools.py
async def tool_name(arguments: Dict[str, Any]) -> Dict[str, Any]:
    # Extract parameters
    param = arguments.get("param_name")
    if not param:
        raise ValueError("param_name is required")
    
    # Call database function
    result = database_function(param)
    
    # Return MCP-compliant response
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(result, indent=2)
            }
        ]
    }
```

### Project Context Handling
- Agents provide project info as: git remote URL (preferred) or absolute path
- `get_project_id()` creates deterministic hash for database scoping
- All operations require `project_id` parameter for isolation

## Critical Implementation Details

### Completion Summary Logic
In `database.py`, completed sections get replaced with summaries:
- Completed subtasks → Task shows "✓ All subtasks completed"  
- Completed tasks → Phase shows "✓ All tasks completed"
- Parents remain visible even when all children are completed

### Hierarchy Constraints (database.py)
- Projects can contain: phases, tasks
- Phases can contain: tasks, subtasks  
- Tasks can contain: subtasks
- Subtasks cannot contain children
- All operations validate these rules

### Status Transitions
- `not_started` → `in_progress` → `completed`
- Rolling work plan filters out `completed` items
- Completed items only appear as parent summaries

## Testing & Validation

### Required Test Pattern
```bash
# Always test with uv run
uv run python -c "from database import init_database; init_database()"
uv run python -c "from project_id import get_project_id; print(get_project_id('test'))"
```

### Token Efficiency Targets
- Single task operations: <100 tokens
- Current work plan: <500 tokens  
- 80%+ reduction vs file-based task management

## Common Patterns & Gotchas

- **Never bypass UV**: All Python execution must use `uv run`
- **Project isolation**: Always pass and validate `project_id`  
- **Subtask completion**: Follow the 6-step workflow religiously with dual approval gates
- **Never auto-progress**: Always wait for explicit human approval at steps 4 and 6
- **Hierarchy building**: Use `build_hierarchy()` from `database.py` for nested structures
- **Error handling**: MCP tools must return proper error responses, not raise exceptions

## Quick Reference Commands
```bash
# Setup & Dependencies  
uv sync                                    # Install dependencies
uv run python -c "from database import init_database; init_database()"  # Initialize DB

# Testing Key Components
uv run python project_id.py              # Test project ID generation
uv run python -c "import database; print('DB connection OK')"  # Test DB

# Development
uv add mcp                                # Add MCP dependency (already done)
```
