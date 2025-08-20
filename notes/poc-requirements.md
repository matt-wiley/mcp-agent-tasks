# MCP Task Management Server - POC Implementation Guide

## Overview
Build a minimal MCP server that lets AI agents manage tasks without burning context tokens. Focus: prove the "rolling work plan" concept works and saves tokens.

## What We're Proving
1. **Agent can use the tools naturally** - no manual MCP wrestling
2. **Massive token savings** - current work plans vs file-based task lists
3. **Rolling work plan works** - completed items auto-hide, focus maintained

## Core Implementation - Keep It Simple

### Database: Single SQLite File
**Location:** `./tasks.db` (same directory as MCP server script)

**Tables:**
```sql
-- Work items table
CREATE TABLE work_items (
    id INTEGER PRIMARY KEY,
    project_id TEXT NOT NULL,  -- Base64 encoded project identifier
    type TEXT NOT NULL CHECK (type IN ('project', 'phase', 'task', 'subtask')),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'not_started' 
        CHECK (status IN ('not_started', 'in_progress', 'completed')),
    parent_id INTEGER REFERENCES work_items(id),
    notes TEXT,
    order_index REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Simple audit log  
CREATE TABLE changelog (
    id INTEGER PRIMARY KEY,
    work_item_id INTEGER,
    project_id TEXT,
    action TEXT,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Basic indexes
CREATE INDEX idx_project ON work_items(project_id);
CREATE INDEX idx_parent ON work_items(parent_id);
CREATE INDEX idx_status ON work_items(status);
```

### MCP Tools - Minimum Viable Set

#### 1. `get_project_id(project_info)`
**Returns:** Deterministic project ID hash for given project information

**Parameters:**
- `project_info` (string): Git remote URL (preferred) or absolute path to project root

**Agent Usage Guide:**
The agent should provide project context in this priority order:
1. Git remote URL: `"https://github.com/user/repo.git"`
2. Absolute path to project root: `"/Users/dev/myproject"`

**Logic:**
- Takes input string and returns `base64.encode(project_info)`
- Pure function - no file system access by MCP server

**Response format:**
```json
{
  "project_id": "aHR0cHM6Ly9naXRodWIuY29tL3VzZXIvcmVwby5naXQ=",
  "raw_value": "https://github.com/user/repo.git"
}
```

#### 2. `get_current_work_plan(project_id)`
**Returns:** JSON hierarchy of incomplete work items only

**Parameters:**
- `project_id` (required): Project identifier from `get_project_id()`

**Logic:** 
- Show items with incomplete status (`not_started`, `in_progress`)
- Hide completed subtasks, show parent task summary
- Hide completed tasks, show parent phase summary  
- Projects always visible (top level containers)

**Response format:**
```json
{
  "projects": [
    {
      "id": 1,
      "title": "Website Redesign",
      "type": "project",
      "status": "in_progress",
      "phases": [
        {
          "id": 2,
          "title": "Research Phase", 
          "type": "phase",
          "status": "completed",
          "summary": "✓ All tasks completed"
        },
        {
          "id": 3,
          "title": "Design Phase",
          "type": "phase", 
          "status": "in_progress",
          "tasks": [
            {
              "id": 4,
              "title": "Create wireframes",
              "type": "task",
              "status": "in_progress"
            }
          ]
        }
      ]
    }
  ]
}
```

#### 2. `create_work_item(type, title, description, parent_id)`
**Creates new work item**
- Auto-assigns order_index (max sibling + 10)
- Logs creation to changelog
- Returns created item with ID

#### 3. `update_work_item(id, **fields)`  
**Updates any fields on a work item**
- Logs changes to changelog
- Returns updated item

#### 4. `complete_item(id)`
**Marks item as completed**
- Sets status = 'completed' 
- Logs completion
- Returns confirmation

#### 6. `search_items(query, project_id)`
**Simple text search across title/description**
- `project_id` (required): Project identifier from `get_project_id()`
- Basic LIKE '%query%' search within project scope
- Returns matching items with parent context

### File Structure - Single Directory Deploy
```
mcp-task-server/
├── server.py          # Main MCP server script
├── database.py        # SQLite operations  
├── tasks.db          # SQLite database (created on first run)
├── requirements.txt   # Python dependencies
└── README.md         # Setup instructions
```

## Implementation Decisions - Simplest Possible

### Project ID Logic - Pure Hash Function
**Goal:** Consistent project identifier from agent-provided context

**Implementation:**
```python
import base64

def get_project_id(project_info):
    """
    Pure function: convert project info string to consistent ID
    
    Args:
        project_info (str): Git remote URL or absolute project path
        
    Returns:
        dict: {"project_id": "base64hash", "raw_value": "input"}
    """
    project_id = base64.b64encode(project_info.encode()).decode()
    return {
        "project_id": project_id,
        "raw_value": project_info
    }
```

**Agent Responsibility:**
The agent determines project context from its environment:
1. Check for git remote: `git remote get-url origin`
2. Fall back to current directory path
3. Call `get_project_id(determined_project_info)`
4. Use returned project_id in all subsequent tool calls

**Benefits:**
- MCP server is stateless - no file system access required
- Same project info always generates same ID
- Agent controls project context determination
- **Max depth:** 4 levels (Project > Phase > Task > Subtask)
- **Hierarchy rules:** Project → Phase/Task, Phase → Task, Task → Subtask
- **No cycles:** Simple parent chain validation (max 4 lookups)
- **No field limits:** Let SQLite handle it

### Data Rules (Enforced in Code)
**Show Rule:** Display incomplete items, summarize completed sections
```python
def get_current_work_plan():
    # Pseudo-code
    projects = get_all_projects()
    for project in projects:
        project.phases = get_incomplete_phases_or_summaries(project.id)
        for phase in project.phases:
            if phase.status != 'completed':
                phase.tasks = get_incomplete_tasks_or_summaries(phase.id)
    return projects
```

### Error Handling - Basic Only
- Return simple error messages in MCP response format
- Log errors to console for debugging
- No retry logic, no graceful degradation

### Configuration - Hardcoded
- Database path: `./tasks.db`
- No config files, no environment variables
- All behavior hardcoded for simplicity

## Testing Plan

### Phase 1: Basic Function Test (30 minutes)
**Setup:**
1. Start MCP server in a git repository directory
2. Connect Claude to MCP server
3. Verify all 6 tools are discoverable

**Test Script:**
```
Agent prompt: "Determine the current project context (git remote or directory path), get a project ID for it, then create a project called 'Test Project' with a phase called 'Phase 1' containing a task called 'Task 1'. Show me the current work plan."

Expected: 
- Agent determines project context from its environment
- Agent calls get_project_id() with the determined context
- Hierarchical display showing project > phase > task structure
- All items scoped to the provided project ID
```

### Phase 2: Rolling Work Plan Test (20 minutes)
**Test rolling behavior:**
1. Create project with 2 phases, each with 2 tasks (all within auto-detected project ID)
2. Complete all tasks in phase 1
3. Call `get_current_work_plan()`
4. **Expected:** Phase 1 shows as "✓ All tasks completed", Phase 2 shows individual tasks

**Test project isolation:**
1. Agent determines different project context (different directory or git remote)
2. Agent calls `get_project_id()` with new context - should return different project ID
3. Call `get_current_work_plan(new_project_id)` - should show empty (no items for this project)

**Test completion:**
```
Agent prompt: "Complete all remaining tasks and show the final work plan."

Expected: Clean summary view, no task clutter, scoped to current project
```

### Phase 3: Token Usage Measurement (15 minutes)
**Baseline measurement:**
1. Create equivalent task structure in a text file
2. Count tokens when agent reads entire file for single task update
3. **Baseline:** Estimate 1000+ tokens for context loading

**POC measurement:**  
1. Use `complete_item(id)` to mark one task complete
2. Count tokens in request + response
3. **Target:** Under 100 tokens for single task update

**Success criteria:** 80%+ token reduction vs file-based approach

### Phase 4: Agent Workflow Test (30 minutes)
**Natural usage test:**
```
Agent prompt: "Help me plan a small website project. Create a project structure, then work through completing some tasks while keeping me updated on progress."
```

**Observe:**
- Does agent use tools naturally?
- Does rolling work plan maintain focus?
- Any confusion or friction points?

### Phase 5: Edge Case Testing (15 minutes)
**Quick validation:**
1. Try to create circular parent relationship (should fail)
2. Delete item with children (should fail)
3. Search for items (should return results)
4. Check changelog has entries

## Success Metrics - Simple Pass/Fail

### Core Functionality ✅/❌
- [ ] All MCP tools work without errors
- [ ] Project ID generated consistently from agent-provided project info
- [ ] Agent determines project context and provides it to MCP server
- [ ] Agent can create hierarchical work structures within project scope
- [ ] Rolling work plan hides completed sections
- [ ] Search returns relevant results within project scope
- [ ] Basic audit trail captured with project ID
- [ ] Different directories show different project contexts

### Token Efficiency ✅/❌  
- [ ] Single task operations use <100 tokens
- [ ] 80%+ reduction vs file-based task management
- [ ] Current work plan stays under 500 tokens for typical project

### Agent Experience ✅/❌
- [ ] Agent uses tools without prompting or confusion
- [ ] Work plan updates feel immediate and focused
- [ ] No need for manual work plan migration between contexts

## Implementation Notes for Junior Dev

### Getting Started
1. **Use existing MCP Python library** - don't build protocol from scratch
2. **SQLite with Python sqlite3** - no external dependencies
3. **Start with hardcoded test data** - create sample project in database on first run
4. **Test each tool individually** before building complex workflows

### Key Implementation Tips
- **MCP tool responses:** Always return JSON, handle errors gracefully
- **Database:** Use context managers (`with sqlite3.connect()`)
- **Rolling logic:** Start simple, get basic filtering working first
- **Testing:** Use Claude Desktop with MCP config to test tools directly

### What NOT to Worry About
- Performance optimization
- Security or authentication  
- Multi-user scenarios
- Error recovery or resilience
- Production deployment concerns
- Advanced SQL optimization

## Delivery Checklist

**MVP Complete When:**
- [ ] 6 MCP tools implemented and working (including pure `get_project_id()`)
- [ ] Project ID generation from agent-provided project context
- [ ] Rolling work plan logic functional with project scoping
- [ ] Basic SQLite schema created with project_id field
- [ ] Token usage reduction demonstrated
- [ ] Agent can complete workflow test successfully
- [ ] Project isolation verified (different project contexts = different data)
- [ ] 30-second demo ready: "Watch this task update use 50 tokens instead of 1000"

**Time Estimate:** 2-3 days for junior developer

---

*This POC proves the core concept with minimal complexity. If successful, Phase 2 can add polish, optimization, and production features.*