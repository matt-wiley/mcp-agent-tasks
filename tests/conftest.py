"""
Test configuration and fixtures for MCP Task Management Server tests.
"""

import pytest
import os
import sys
import tempfile
import sqlite3
from pathlib import Path

# Add the parent directory to Python path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import init_database, get_connection, DATABASE_PATH
from project_id import get_project_id as get_project_id_func

# Test database path - use a temporary file for tests
TEST_DB_PATH = None

@pytest.fixture(scope="function")
def test_db():
    """
    Create a temporary database for each test function.
    This ensures test isolation and prevents test data pollution.
    """
    global TEST_DB_PATH
    
    # Create a temporary database file
    fd, TEST_DB_PATH = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Temporarily patch the database path
    original_path = DATABASE_PATH
    import database
    database.DATABASE_PATH = TEST_DB_PATH
    
    # Initialize the test database
    init_database()
    
    yield TEST_DB_PATH
    
    # Cleanup: restore original path and remove temp file
    database.DATABASE_PATH = original_path
    try:
        os.unlink(TEST_DB_PATH)
    except OSError:
        pass

@pytest.fixture
def sample_project_id():
    """Generate a consistent test project ID."""
    return get_project_id_func("test_project_path")['project_id']

@pytest.fixture
def sample_work_items():
    """
    Create sample work items for hierarchy testing.
    Returns a list of dictionaries with the expected structure.
    """
    return [
        {
            'id': 1,
            'type': 'project', 
            'title': 'Test Project',
            'description': 'A test project for validation',
            'parent_id': None,
            'status': 'in_progress',
            'project_id': 'dGVzdF9wcm9qZWN0X3BhdGg=',  # base64 for "test_project_path"
            'order_index': 1.0,
            'notes': None
        },
        {
            'id': 2,
            'type': 'phase',
            'title': 'Phase 1', 
            'description': 'First phase',
            'parent_id': 1,
            'status': 'in_progress',
            'project_id': 'dGVzdF9wcm9qZWN0X3BhdGg=',
            'order_index': 1.0,
            'notes': None
        },
        {
            'id': 3,
            'type': 'task',
            'title': 'Task 1',
            'description': 'First task in phase 1', 
            'parent_id': 2,
            'status': 'completed',
            'project_id': 'dGVzdF9wcm9qZWN0X3BhdGg=',
            'order_index': 1.0,
            'notes': None
        },
        {
            'id': 4,
            'type': 'subtask',
            'title': 'Subtask 1.1',
            'description': 'First subtask',
            'parent_id': 3,
            'status': 'completed',
            'project_id': 'dGVzdF9wcm9qZWN0X3BhdGg=',
            'order_index': 1.0,
            'notes': None
        },
        {
            'id': 5,
            'type': 'subtask', 
            'title': 'Subtask 1.2',
            'description': 'Second subtask',
            'parent_id': 3,
            'status': 'completed',
            'project_id': 'dGVzdF9wcm9qZWN0X3BhdGg=',
            'order_index': 2.0,
            'notes': None
        },
        {
            'id': 6,
            'type': 'task',
            'title': 'Task 2', 
            'description': 'Direct task under project',
            'parent_id': 1,  # Direct under project
            'status': 'not_started',
            'project_id': 'dGVzdF9wcm9qZWN0X3BhdGg=',
            'order_index': 2.0,
            'notes': None
        }
    ]

@pytest.fixture
def populated_db(test_db, sample_work_items, sample_project_id):
    """
    Create a database populated with sample work items.
    """
    # Patch the database path for our database module
    import database
    original_path = database.DATABASE_PATH
    database.DATABASE_PATH = test_db
    
    # Insert sample data
    with get_connection() as conn:
        for item in sample_work_items:
            conn.execute('''
                INSERT INTO work_items (
                    id, project_id, type, title, description, status, parent_id, 
                    order_index, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', [
                item['id'], item['project_id'], item['type'], item['title'],
                item['description'], item['status'], item['parent_id'],
                item['order_index'], item['notes']
            ])
        conn.commit()
    
    yield test_db
    
    # Restore original path
    database.DATABASE_PATH = original_path
