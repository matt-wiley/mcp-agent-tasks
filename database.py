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


if __name__ == "__main__":
    # Test database initialization when run directly
    logging.basicConfig(level=logging.INFO)
    init_database()
    print(f"Database initialized at: {DATABASE_PATH}")
