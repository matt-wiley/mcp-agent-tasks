# MCP Task Management Server - Implementation Plan

**Project:** MCP Agent Tasks  
**Repository:** https://github.com/matt-wiley/mcp-agent-tasks  
**Goal:** Build a minimal MCP server for AI agents to manage tasks without burning context tokens

## Project Overview

This implementation plan breaks down the POC requirements into a hierarchical task structure. The goal is to prove three key concepts:
1. Agents can use the tools naturally
2. Massive token savings vs current work plans
3. Rolling work plan concept works (completed items auto-hide)

---

## Phase 1: Project Setup & Foundation

### Task 1.1: Python Project Setup with UV
**Goal:** Initialize the project using UV package manager

#### Subtask 1.1.1: Initialize UV project
- [x] Run `uv init` to create pyproject.toml
- [x] Configure project metadata (name, version, description)
- [x] Set minimum Python version requirement
- [x] Add basic project structure for MCP server

#### Subtask 1.1.2: Add MCP dependencies with UV
- [x] Research and add MCP Python library dependency with `uv add`
- [x] Add any additional dependencies needed for MCP server
- [x] Document that SQLite3 is built-in (no dependency needed)
- [x] Update .gitignore to exclude `tasks.db`, `.venv/`, `__pycache__`, etc.

### Task 1.2: Database Schema Implementation
**Goal:** Create the SQLite database structure for task management

#### Subtask 1.2.1: Create database.py module
- [ ] Create `database.py` file in project root
- [ ] Import required SQLite and datetime modules
- [ ] Define database file path constant (`./tasks.db`)

#### Subtask 1.2.2: Implement work_items table creation
- [ ] Write SQL schema for work_items table with all specified columns
- [ ] Add type constraints (project, phase, task, subtask)
- [ ] Add status constraints (not_started, in_progress, completed)
- [ ] Add foreign key constraint for parent_id
- [ ] Add default values for status, order_index, timestamps

#### Subtask 1.2.3: Implement changelog table creation
- [ ] Write SQL schema for changelog table
- [ ] Add all required columns (id, work_item_id, project_id, action, details, created_at)
- [ ] Set up proper data types and constraints

#### Subtask 1.2.4: Create database indexes
- [ ] Create index on project_id column
- [ ] Create index on parent_id column  
- [ ] Create index on status column
- [ ] Write function to create all indexes

#### Subtask 1.2.5: Database initialization function
- [ ] Write `init_database()` function to create tables and indexes
- [ ] Add error handling for database creation
- [ ] Ensure function is idempotent (safe to run multiple times)
- [ ] Add logging for database initialization steps

---

## Phase 2: Core MCP Tools Implementation

### Task 2.1: Project ID Management Tool
**Goal:** Implement the pure function for generating consistent project IDs

#### Subtask 2.1.1: Create get_project_id function
- [ ] Implement base64 encoding of project info string
- [ ] Return both project_id and raw_value in response format
- [ ] Add input validation (non-empty string)
- [ ] Write unit tests for consistent ID generation

#### Subtask 2.1.2: Integrate get_project_id with MCP server
- [ ] Register tool with MCP server framework
- [ ] Define MCP tool schema with project_info parameter
- [ ] Add proper error handling and response formatting
- [ ] Test tool registration and basic functionality

### Task 2.2: Work Plan Retrieval Tool
**Goal:** Implement the rolling work plan that hides completed items

#### Subtask 2.2.1: Basic work plan query
- [ ] Write SQL query to get all work items for a project_id
- [ ] Filter to show only incomplete items (not_started, in_progress)
- [ ] Order items by hierarchy and order_index
- [ ] Return basic flat list first (before hierarchy logic)

#### Subtask 2.2.2: Implement hierarchy building logic
- [ ] Create function to build nested project → phase → task → subtask structure
- [ ] Group items by type and parent_id relationships
- [ ] Handle orphaned items (items with invalid parent_id)
- [ ] Ensure consistent ordering within each level

#### Subtask 2.2.3: Add completion summaries for completed sections
- [ ] Detect completed phases/tasks that have completed children
- [ ] Generate summary text ("✓ All tasks completed")
- [ ] Include completion summaries in hierarchy
- [ ] Maintain parent visibility even when all children completed

#### Subtask 2.2.4: Integrate get_current_work_plan with MCP
- [ ] Register tool with MCP server
- [ ] Define MCP tool schema with project_id parameter
- [ ] Format response as specified JSON structure
- [ ] Add comprehensive error handling

### Task 2.3: Work Item Creation Tool
**Goal:** Allow agents to create new work items in the hierarchy

#### Subtask 2.3.1: Basic work item insertion
- [ ] Write SQL INSERT for work_items table
- [ ] Auto-generate order_index (max sibling + 10)
- [ ] Set created_at and updated_at timestamps
- [ ] Return created item with generated ID

#### Subtask 2.3.2: Hierarchy validation
- [ ] Validate type restrictions (project → phase/task, phase → task, etc.)
- [ ] Check parent_id exists and is valid type for hierarchy
- [ ] Prevent circular references (max 4-level depth check)
- [ ] Validate parent belongs to same project

#### Subtask 2.3.3: Changelog integration
- [ ] Log creation action to changelog table
- [ ] Include project_id, action type, and details
- [ ] Add timestamp for audit trail
- [ ] Handle logging errors gracefully

#### Subtask 2.3.4: MCP tool integration
- [ ] Register create_work_item tool with server
- [ ] Define schema: type, title, description, parent_id parameters
- [ ] Add validation for required fields
- [ ] Format response with created item data

### Task 2.4: Work Item Update Tool
**Goal:** Allow modification of existing work items

#### Subtask 2.4.1: Generic update mechanism
- [ ] Write flexible SQL UPDATE that accepts any field updates
- [ ] Update updated_at timestamp automatically
- [ ] Validate updated fields against table schema
- [ ] Return updated item with all current values

#### Subtask 2.4.2: Update validation logic
- [ ] Prevent changing project_id (maintain project isolation)
- [ ] Validate status transitions are logical
- [ ] Validate type changes don't break hierarchy rules
- [ ] Ensure parent_id changes maintain valid hierarchy

#### Subtask 2.4.3: Changelog for updates
- [ ] Log each field change to changelog
- [ ] Include old and new values in details
- [ ] Track which fields were modified
- [ ] Handle multiple field updates in single operation

#### Subtask 2.4.4: MCP tool integration
- [ ] Register update_work_item tool
- [ ] Define schema with id parameter and flexible field updates
- [ ] Add proper error handling for invalid IDs
- [ ] Format response with updated item

### Task 2.5: Item Completion Tool
**Goal:** Specialized tool for marking items as completed

#### Subtask 2.5.1: Completion logic
- [ ] Update item status to 'completed'
- [ ] Set updated_at timestamp
- [ ] Validate item exists and belongs to project
- [ ] Return confirmation with completion timestamp

#### Subtask 2.5.2: Completion changelog
- [ ] Log completion action to changelog
- [ ] Include completion timestamp in details
- [ ] Add project_id for proper scoping
- [ ] Handle logging errors

#### Subtask 2.5.3: MCP tool integration
- [ ] Register complete_item tool with server
- [ ] Define schema with id parameter
- [ ] Add validation for item existence
- [ ] Return completion confirmation

### Task 2.6: Search Tool Implementation
**Goal:** Allow text search across work items within project scope

#### Subtask 2.6.1: Basic search query
- [ ] Write SQL query with LIKE '%query%' for title and description
- [ ] Filter by project_id to maintain project isolation
- [ ] Return matching items with basic information
- [ ] Add case-insensitive search

#### Subtask 2.6.2: Add parent context to search results
- [ ] Include parent item information for each search result
- [ ] Build breadcrumb path (project → phase → task → subtask)
- [ ] Handle orphaned items in search results
- [ ] Format parent context clearly

#### Subtask 2.6.3: MCP tool integration
- [ ] Register search_items tool
- [ ] Define schema with query and project_id parameters
- [ ] Add input validation (non-empty query)
- [ ] Format search results consistently

---

## Phase 3: MCP Server Implementation

### Task 3.1: Main Server Script
**Goal:** Create the main MCP server that ties everything together

#### Subtask 3.1.1: Server framework setup
- [ ] Research and choose MCP Python library
- [ ] Create `server.py` main script in project root
- [ ] Initialize MCP server instance
- [ ] Set up basic logging configuration

#### Subtask 3.1.2: Tool registration system
- [ ] Import all tool functions from database module
- [ ] Register all 6 tools with MCP server
- [ ] Define tool schemas and parameters
- [ ] Set up error handling for tool execution

#### Subtask 3.1.3: Database connection management
- [ ] Initialize database on server startup
- [ ] Create connection pooling or context managers
- [ ] Handle database errors gracefully
- [ ] Add database health check endpoint if supported

#### Subtask 3.1.4: Server startup and shutdown
- [ ] Add command-line argument parsing if needed
- [ ] Implement graceful shutdown handling
- [ ] Add server status logging
- [ ] Create main() function and entry point

---

## Phase 4: Testing & Validation

### Task 4.1: Unit Testing
**Goal:** Ensure individual components work correctly

#### Subtask 4.1.1: Database function tests
- [ ] Test database initialization (create tables, indexes)
- [ ] Test work item CRUD operations
- [ ] Test changelog creation
- [ ] Test project ID generation consistency

#### Subtask 4.1.2: Hierarchy validation tests
- [ ] Test valid hierarchy creation (project → phase → task → subtask)
- [ ] Test hierarchy constraint violations
- [ ] Test circular reference prevention
- [ ] Test orphaned item handling

#### Subtask 4.1.3: Rolling work plan tests
- [ ] Test work plan with all incomplete items
- [ ] Test work plan with mixed completion states
- [ ] Test completion summary generation
- [ ] Test empty project work plan

### Task 4.2: Integration Testing
**Goal:** Test complete workflows through MCP interface

#### Subtask 4.2.1: Basic function test (as per POC requirements)
- [ ] Start MCP server in git repository
- [ ] Connect Claude to MCP server
- [ ] Verify all 6 tools are discoverable
- [ ] Run complete test script from POC requirements

#### Subtask 4.2.2: Rolling work plan test
- [ ] Create project with hierarchical structure
- [ ] Complete various items and verify rolling behavior
- [ ] Test project isolation with different project contexts
- [ ] Verify completion summaries appear correctly

#### Subtask 4.2.3: Token usage measurement
- [ ] Measure baseline (file-based approach)
- [ ] Measure POC approach for equivalent operations
- [ ] Document token savings achieved
- [ ] Verify 80%+ reduction target is met

### Task 4.3: Agent Workflow Testing
**Goal:** Ensure natural agent interaction

#### Subtask 4.3.1: Natural usage test
- [ ] Give agent open-ended project planning prompt
- [ ] Observe tool usage patterns and friction points
- [ ] Document any confusion or sub-optimal interactions
- [ ] Verify work plan maintains focus during workflow

#### Subtask 4.3.2: Edge case testing
- [ ] Test circular reference attempts
- [ ] Test item deletion with children
- [ ] Test search functionality thoroughly
- [ ] Verify changelog entries are created properly

---

## Phase 5: Documentation & Deployment Preparation

### Task 5.1: Documentation
**Goal:** Provide clear setup and usage instructions

#### Subtask 5.1.1: README.md creation
- [ ] Write clear setup instructions
- [ ] Document MCP client configuration
- [ ] Add example usage scenarios
- [ ] Include troubleshooting section

#### Subtask 5.1.2: API documentation
- [ ] Document all 6 MCP tools with parameters and responses
- [ ] Provide example tool calls and responses
- [ ] Document error conditions and responses
- [ ] Create quick reference guide

### Task 5.2: Demo Preparation
**Goal:** Create compelling demonstration of token savings

#### Subtask 5.2.1: Demo script creation
- [ ] Create 30-second demo scenario
- [ ] Prepare before/after token usage comparison
- [ ] Document specific token counts for key operations
- [ ] Create visual comparison (if possible)

#### Subtask 5.2.2: Performance validation
- [ ] Measure actual token usage in realistic scenarios
- [ ] Verify single task operations use <100 tokens
- [ ] Confirm work plans stay under 500 tokens
- [ ] Document performance characteristics

---

## Success Criteria Checklist

### Core Functionality
- [ ] All 6 MCP tools work without errors
- [ ] Project ID generated consistently from agent-provided project info
- [ ] Agent can create hierarchical work structures within project scope
- [ ] Rolling work plan hides completed sections
- [ ] Search returns relevant results within project scope
- [ ] Basic audit trail captured with project ID
- [ ] Different directories show different project contexts

### Token Efficiency
- [ ] Single task operations use <100 tokens
- [ ] 80%+ reduction vs file-based task management
- [ ] Current work plan stays under 500 tokens for typical project

### Agent Experience
- [ ] Agent uses tools without prompting or confusion
- [ ] Work plan updates feel immediate and focused
- [ ] No need for manual work plan migration between contexts

## Updated Project Structure

**Note:** Unlike the original POC requirements which suggested a `mcp-task-server/` subdirectory, this implementation works from the project root using UV for dependency management.

**File Structure:**
```
mcp-agent-tasks/            # Project root
├── server.py               # Main MCP server script
├── database.py             # SQLite operations  
├── tasks.db               # SQLite database (created on first run)
├── pyproject.toml          # UV project configuration and dependencies
├── README.md              # Existing README (update as needed)
├── .venv/                 # UV virtual environment (gitignored)
└── notes/                 # Existing notes directory
    └── poc-requirements.md
```

## Estimated Timeline
- **Phase 1:** 0.5 days (Project setup)
- **Phase 2:** 2 days (Core MCP tools)
- **Phase 3:** 0.5 days (Server implementation)
- **Phase 4:** 1 day (Testing & validation)
- **Phase 5:** 0.5 days (Documentation & demo)

**Total:** 4.5 days for complete implementation

## Next Steps
1. Begin with Phase 1, Task 1.1 (Repository Structure Setup)
2. Complete each subtask in order, testing as you go
3. Use this document to track progress and check off completed items
4. Refer back to POC requirements for specific implementation details
