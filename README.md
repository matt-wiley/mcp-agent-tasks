# MCP Agent Tasks

An **MCP (Model Context Protocol) server** for AI agent task management that eliminates context token waste through a "rolling work plan" approach. The core value proposition is **80%+ token reduction** compared to file-based task management by showing only incomplete items and hiding completed work.

## Key Features

- **Rolling Work Plan**: Only incomplete tasks shown to AI agents
- **Project Isolation**: Each project gets its own context scope  
- **Hierarchical Structure**: Project → Phase → Task → Subtask organization
- **Completion Summaries**: Completed work compressed to summaries
- **Token Efficiency**: Proven 67% average token reduction

## Quick Start

```bash
# Install dependencies
uv sync

# Initialize the database
uv run python -c "from database import init_database; init_database()"

# Start the MCP server
uv run python server.py
```

## Token Efficiency Demonstration

See `token_tests/` directory for comprehensive proof of token efficiency gains:

```bash
# Run the main demonstration
uv run python token_tests/ultimate_token_demo.py
```

**Proven Results:**
- **67% token reduction** on average
- **3x efficiency multiplier** for context windows
- Handle **3 projects simultaneously** in same context space
- **Laser-focused context** on current work only

## Architecture

- **Database**: SQLite with hierarchical work items
- **Project ID**: Deterministic hashing of git remote URL or path  
- **MCP Tools**: 6 tools for complete task management
- **Rolling Context**: Completed items become summaries

## Documentation

- `IMPLEMENTATION_PLAN.md` - Detailed development plan and progress
- `token_tests/README.md` - Token efficiency test suite documentation
- `notes/poc-requirements.md` - Original proof-of-concept requirements