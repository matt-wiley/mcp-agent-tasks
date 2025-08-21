"""
Database module for MCP Task Management Server

Handles SQLite operations for work items and changelog management.
Implements the database schema as specified in the POC requirements.
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

# Database file path constant
DATABASE_PATH = "./tasks.db"

# Set up logging
logger = logging.getLogger(__name__)


def get_connection() -> sqlite3.Connection:
    """
    Get a connection to the SQLite database.
    
    Returns:
        sqlite3.Connection: Database connection with row factory set
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


def init_database() -> None:
    """
    Initialize the database with required tables and indexes.
    This function is idempotent and safe to run multiple times.
    """
    logger.info("Initializing database...")
    
    with get_connection() as conn:
        # Create work_items table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS work_items (
                id INTEGER PRIMARY KEY,
                project_id TEXT NOT NULL,
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
            )
        ''')
        
        # Create changelog table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS changelog (
                id INTEGER PRIMARY KEY,
                work_item_id INTEGER,
                project_id TEXT,
                action TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        conn.execute('CREATE INDEX IF NOT EXISTS idx_project ON work_items(project_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_parent ON work_items(parent_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_status ON work_items(status)')
        
        conn.commit()
        logger.info("Database initialization complete")


def get_work_items_for_project(project_id: str, status_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Get all work items for a project, optionally filtered by status.
    
    Args:
        project_id: Project identifier
        status_filter: List of statuses to include (default: incomplete items only)
    
    Returns:
        List of work items as dictionaries
    """
    if status_filter is None:
        status_filter = ['not_started', 'in_progress']
    
    with get_connection() as conn:
        # Build query with status filter
        placeholders = ','.join('?' for _ in status_filter)
        query = f"""
            SELECT id, project_id, type, title, description, status, parent_id, 
                   notes, order_index, created_at, updated_at
            FROM work_items 
            WHERE project_id = ? AND status IN ({placeholders})
            ORDER BY 
                CASE type 
                    WHEN 'project' THEN 1 
                    WHEN 'phase' THEN 2 
                    WHEN 'task' THEN 3 
                    WHEN 'subtask' THEN 4 
                END,
                order_index ASC,
                created_at ASC
        """
        
        params = [project_id] + status_filter
        cursor = conn.execute(query, params)
        
        # Convert rows to dictionaries
        items = []
        for row in cursor.fetchall():
            items.append(dict(row))
        
        logger.info(f"Retrieved {len(items)} work items for project {project_id}")
        return items


def get_all_work_items_for_project(project_id: str) -> List[Dict[str, Any]]:
    """
    Get ALL work items for a project regardless of status.
    Used for building completion summaries.
    
    Args:
        project_id: Project identifier
    
    Returns:
        List of all work items as dictionaries
    """
    with get_connection() as conn:
        query = """
            SELECT id, project_id, type, title, description, status, parent_id, 
                   notes, order_index, created_at, updated_at
            FROM work_items 
            WHERE project_id = ?
            ORDER BY 
                CASE type 
                    WHEN 'project' THEN 1 
                    WHEN 'phase' THEN 2 
                    WHEN 'task' THEN 3 
                    WHEN 'subtask' THEN 4 
                END,
                order_index ASC,
                created_at ASC
        """
        
        cursor = conn.execute(query, [project_id])
        
        # Convert rows to dictionaries
        items = []
        for row in cursor.fetchall():
            items.append(dict(row))
        
        logger.info(f"Retrieved {len(items)} total work items for project {project_id}")
        return items


if __name__ == "__main__":
    # Test database initialization and queries when run directly
    logging.basicConfig(level=logging.INFO)
    
    # Initialize database
    init_database()
    print(f"Database initialized at: {DATABASE_PATH}")
    
    # Test queries with empty database
    test_project_id = "dGVzdF9wcm9qZWN0"  # base64 for "test_project"
    
    print("\nTesting queries on empty database:")
    incomplete_items = get_work_items_for_project(test_project_id)
    print(f"Incomplete items found: {len(incomplete_items)}")
    
    all_items = get_all_work_items_for_project(test_project_id)
    print(f"All items found: {len(all_items)}")
    
    # Test with different status filters
    completed_items = get_work_items_for_project(test_project_id, ['completed'])
    print(f"Completed items found: {len(completed_items)}")
    
    print("\nDatabase query functions working correctly!")
