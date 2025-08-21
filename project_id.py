"""
Project ID management for MCP Task Management Server

Provides pure functions for generating consistent project identifiers
from agent-provided project context information.
"""

import base64
from typing import Dict


def get_project_id(project_info: str) -> Dict[str, str]:
    """
    Pure function: convert project info string to consistent ID
    
    Args:
        project_info (str): Git remote URL or absolute project path
        
    Returns:
        dict: {"project_id": "base64hash", "raw_value": "input"}
        
    Example:
        >>> get_project_id("https://github.com/user/repo.git")
        {
            "project_id": "aHR0cHM6Ly9naXRodWIuY29tL3VzZXIvcmVwby5naXQ=",
            "raw_value": "https://github.com/user/repo.git"
        }
    """
    if not project_info or not isinstance(project_info, str):
        raise ValueError("project_info must be a non-empty string")
    
    # Convert project info string to consistent base64 ID
    project_id = base64.b64encode(project_info.encode('utf-8')).decode('ascii')
    
    return {
        "project_id": project_id,
        "raw_value": project_info
    }


if __name__ == "__main__":
    # Test the function when run directly
    test_cases = [
        "https://github.com/matt-wiley/mcp-agent-tasks.git",
        "/home/matt/Repospace/com/github/matt-wiley/mcp-agent-tasks",
        "https://github.com/user/repo.git",
    ]
    
    print("Testing get_project_id function:")
    for test_case in test_cases:
        result = get_project_id(test_case)
        print(f"\nInput: {test_case}")
        print(f"Project ID: {result['project_id']}")
        print(f"Raw Value: {result['raw_value']}")
        
        # Verify consistency by calling again
        result2 = get_project_id(test_case)
        assert result == result2, "Function must be deterministic"
        print("✓ Consistency verified")
