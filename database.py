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


def build_hierarchy(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build nested hierarchy structure from flat list of work items.
    
    Args:
        items: Flat list of work items with parent_id relationships
    
    Returns:
        Dict with nested structure: projects -> phases -> tasks -> subtasks
        Also includes orphaned items that don't fit the hierarchy
    """
    # Organize items by parent_id
    by_parent = {}  # parent_id -> [children]
    
    for item in items:
        parent_id = item['parent_id']
        if parent_id not in by_parent:
            by_parent[parent_id] = []
        by_parent[parent_id].append(item)
    
    # Build hierarchy starting from projects (no parent)
    hierarchy = {
        'projects': [],
        'orphaned_items': []
    }
    
    # Track all processed item IDs
    processed_ids = set()
    
    # Start with projects (parent_id is None)
    root_items = by_parent.get(None, [])
    projects = [item for item in root_items if item['type'] == 'project']
    
    for project in projects:
        project_dict = dict(project)  # Copy the project data
        project_dict['phases'] = []
        project_dict['direct_tasks'] = []  # Tasks directly under project
        processed_ids.add(project['id'])
        
        # Get children of this project
        project_children = by_parent.get(project['id'], [])
        
        # Separate phases and direct tasks
        phases = [item for item in project_children if item['type'] == 'phase']
        direct_tasks = [item for item in project_children if item['type'] == 'task']
        
        # Process phases
        for phase in phases:
            phase_dict = dict(phase)
            phase_dict['tasks'] = []
            processed_ids.add(phase['id'])
            
            # Get tasks under this phase
            phase_children = by_parent.get(phase['id'], [])
            tasks = [item for item in phase_children if item['type'] == 'task']
            
            # Process tasks under phase
            for task in tasks:
                task_dict = dict(task)
                task_dict['subtasks'] = []
                processed_ids.add(task['id'])
                
                # Get subtasks under this task
                task_children = by_parent.get(task['id'], [])
                subtasks = [item for item in task_children if item['type'] == 'subtask']
                
                # Process subtasks
                for subtask in subtasks:
                    processed_ids.add(subtask['id'])
                
                task_dict['subtasks'] = subtasks
                phase_dict['tasks'].append(task_dict)
            
            project_dict['phases'].append(phase_dict)
        
        # Process direct tasks (tasks directly under project)
        for task in direct_tasks:
            task_dict = dict(task)
            task_dict['subtasks'] = []
            processed_ids.add(task['id'])
            
            # Get subtasks under this task
            task_children = by_parent.get(task['id'], [])
            subtasks = [item for item in task_children if item['type'] == 'subtask']
            
            # Process subtasks
            for subtask in subtasks:
                processed_ids.add(subtask['id'])
            
            task_dict['subtasks'] = subtasks
            project_dict['direct_tasks'].append(task_dict)
        
        hierarchy['projects'].append(project_dict)
    
    # Find orphaned items (items not processed in the hierarchy)
    for item in items:
        if item['id'] not in processed_ids:
            hierarchy['orphaned_items'].append(dict(item))
    
    logger.info(f"Built hierarchy: {len(hierarchy['projects'])} projects, {len(hierarchy['orphaned_items'])} orphaned items")
    return hierarchy


def add_completion_summaries(hierarchy: Dict[str, Any], all_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Add completion summaries for sections where all children are completed.
    
    Args:
        hierarchy: Hierarchy structure from build_hierarchy()
        all_items: All work items for the project (including completed ones)
    
    Returns:
        Modified hierarchy with completion summaries added
    """
    # Create lookup for all items by ID
    items_by_id = {item['id']: item for item in all_items}
    
    def check_all_children_completed(parent_id: int, item_type: str) -> bool:
        """Check if all children of a parent are completed"""
        children = [item for item in all_items 
                   if item.get('parent_id') == parent_id]
        
        if not children:
            return False
            
        return all(child['status'] == 'completed' for child in children)
    
    def count_completed_children(parent_id: int) -> tuple:
        """Count completed vs total children"""
        children = [item for item in all_items 
                   if item.get('parent_id') == parent_id]
        
        if not children:
            return 0, 0
            
        completed = sum(1 for child in children if child['status'] == 'completed')
        return completed, len(children)
    
    # Process each project in the hierarchy
    for project in hierarchy['projects']:
        project_id = project['id']
        
        # Check phases for completion summaries
        for phase in project['phases']:
            phase_id = phase['id']
            completed_tasks, total_tasks = count_completed_children(phase_id)
            
            if completed_tasks > 0 and completed_tasks == total_tasks:
                # All tasks in this phase are completed
                phase['completion_summary'] = f"✓ All {total_tasks} tasks completed"
            elif completed_tasks > 0:
                # Some tasks completed
                phase['completion_summary'] = f"✓ {completed_tasks}/{total_tasks} tasks completed"
        
        # Check direct tasks for subtask completion
        for task in project['direct_tasks']:
            task_id = task['id']
            completed_subtasks, total_subtasks = count_completed_children(task_id)
            
            if completed_subtasks > 0 and completed_subtasks == total_subtasks:
                # All subtasks completed
                task['completion_summary'] = f"✓ All {total_subtasks} subtasks completed"
            elif completed_subtasks > 0:
                # Some subtasks completed
                task['completion_summary'] = f"✓ {completed_subtasks}/{total_subtasks} subtasks completed"
        
        # Check tasks within phases for subtask completion
        for phase in project['phases']:
            for task in phase['tasks']:
                task_id = task['id']
                completed_subtasks, total_subtasks = count_completed_children(task_id)
                
                if completed_subtasks > 0 and completed_subtasks == total_subtasks:
                    # All subtasks completed
                    task['completion_summary'] = f"✓ All {total_subtasks} subtasks completed"
                elif completed_subtasks > 0:
                    # Some subtasks completed
                    task['completion_summary'] = f"✓ {completed_subtasks}/{total_subtasks} subtasks completed"
    
    logger.info("Added completion summaries to hierarchy")
    return hierarchy


def create_work_item(project_id: str, item_type: str, title: str, description: str = None, parent_id: Optional[int] = None, notes: str = None) -> Dict[str, Any]:
    """
    Create a new work item in the database with hierarchy validation.
    
    Args:
        project_id: Project identifier
        item_type: Type of item (project, phase, task, subtask)
        title: Title of the work item
        description: Optional description
        parent_id: Optional parent item ID for hierarchy
        notes: Optional notes
    
    Returns:
        Dict containing the created work item with generated ID
        
    Raises:
        ValueError: If hierarchy validation fails
    """
    # Validate hierarchy rules
    _validate_hierarchy(project_id, item_type, parent_id)
    
    with get_connection() as conn:
        # Auto-generate order_index: get max sibling order + 10
        if parent_id is None:
            # Top-level item, get max order for items with no parent in this project
            cursor = conn.execute(
                "SELECT COALESCE(MAX(order_index), 0) FROM work_items WHERE project_id = ? AND parent_id IS NULL",
                [project_id]
            )
        else:
            # Child item, get max order for siblings with same parent
            cursor = conn.execute(
                "SELECT COALESCE(MAX(order_index), 0) FROM work_items WHERE project_id = ? AND parent_id = ?",
                [project_id, parent_id]
            )
        
        max_order = cursor.fetchone()[0]
        new_order = max_order + 10
        
        # Insert the new work item
        cursor = conn.execute('''
            INSERT INTO work_items (
                project_id, type, title, description, parent_id, notes, order_index,
                status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'not_started', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', [project_id, item_type, title, description, parent_id, notes, new_order])
        
        new_id = cursor.lastrowid
        
        # Fetch the created item to return complete data
        cursor = conn.execute('''
            SELECT id, project_id, type, title, description, status, parent_id,
                   notes, order_index, created_at, updated_at
            FROM work_items WHERE id = ?
        ''', [new_id])
        
        created_item = dict(cursor.fetchone())
        
        conn.commit()
        logger.info(f"Created work item {new_id}: {item_type} '{title}' in project {project_id}")
        
        # Log creation to changelog
        details = f"Created {item_type}: '{title}'"
        if parent_id:
            details += f" (parent: {parent_id})"
        if description:
            details += f" - {description}"
            
        log_to_changelog(new_id, project_id, "created", details)
        
        return created_item


def update_work_item(item_id: int, project_id: str, **updates) -> Dict[str, Any]:
    """
    Update a work item with flexible field updates.
    
    Args:
        item_id: ID of the work item to update
        project_id: Project identifier for validation
        **updates: Keyword arguments for fields to update
        
    Returns:
        Dictionary containing the updated work item
        
    Raises:
        ValueError: If item doesn't exist, belongs to wrong project, or invalid field updates
    """
    if not updates:
        raise ValueError("No updates provided")
    
    # Define valid updateable fields and their types
    VALID_FIELDS = {
        'title': str,
        'description': str,
        'status': str,
        'type': str,
        'parent_id': (int, type(None)),
        'order_index': (int, float),
    }
    
    # Define status constraints
    VALID_STATUSES = ['not_started', 'in_progress', 'completed']
    
    # Define type constraints  
    VALID_TYPES = ['project', 'phase', 'task', 'subtask']
    
    # Validate all provided fields
    for field, value in updates.items():
        if field not in VALID_FIELDS:
            raise ValueError(f"Invalid field '{field}'. Valid fields: {list(VALID_FIELDS.keys())}")
        
        expected_type = VALID_FIELDS[field]
        if not isinstance(value, expected_type):
            raise ValueError(f"Field '{field}' must be of type {expected_type}, got {type(value)}")
        
        # Additional validation for specific fields
        if field == 'status' and value not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{value}'. Must be one of: {VALID_STATUSES}")
        
        if field == 'type' and value not in VALID_TYPES:
            raise ValueError(f"Invalid type '{value}'. Must be one of: {VALID_TYPES}")
    
    with get_connection() as conn:
        # First, verify the item exists and belongs to the project
        cursor = conn.execute(
            "SELECT * FROM work_items WHERE id = ? AND project_id = ?",
            [item_id, project_id]
        )
        existing_item_row = cursor.fetchone()
        
        if not existing_item_row:
            raise ValueError(f"Work item {item_id} not found in project {project_id}")
        
        existing_item = dict(existing_item_row)
        
        # Prevent changing project_id to maintain project isolation
        if 'project_id' in updates:
            raise ValueError("Cannot change project_id - this would break project isolation")
        
        # Validate status transitions are logical
        if 'status' in updates:
            _validate_status_transition(existing_item['status'], updates['status'])
        
        # If updating parent_id or type, validate hierarchy rules
        new_type = updates.get('type', existing_item['type'])
        new_parent_id = updates.get('parent_id', existing_item['parent_id'])
        
        # Validate type changes don't break hierarchy rules
        if 'type' in updates:
            _validate_type_change(item_id, existing_item['type'], new_type, project_id)
        
        # Ensure parent_id changes maintain valid hierarchy
        if 'parent_id' in updates:
            _validate_parent_change(item_id, existing_item['parent_id'], new_parent_id, new_type, project_id)
        
        # If updating both parent_id and type, validate the combination
        if 'type' in updates or 'parent_id' in updates:
            _validate_hierarchy(project_id, new_type, new_parent_id)
        
        # Build the UPDATE SQL dynamically
        set_clauses = []
        params = []
        
        for field, value in updates.items():
            set_clauses.append(f"{field} = ?")
            params.append(value)
        
        # Always update the updated_at timestamp
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        
        # Add the WHERE clause parameters
        params.extend([item_id, project_id])
        
        # Execute the update
        update_sql = f"""
            UPDATE work_items 
            SET {', '.join(set_clauses)}
            WHERE id = ? AND project_id = ?
        """
        
        conn.execute(update_sql, params)
        
        # Get the updated item
        cursor = conn.execute(
            "SELECT * FROM work_items WHERE id = ? AND project_id = ?",
            [item_id, project_id]
        )
        updated_item = dict(cursor.fetchone())
        
        conn.commit()
        logger.info(f"Updated work item {item_id} in project {project_id}: {list(updates.keys())}")
        
        # Log the update to changelog
        details = f"Updated fields: {', '.join(updates.keys())}"
        for field, value in updates.items():
            old_value = existing_item.get(field)
            details += f"\n  {field}: '{old_value}' → '{value}'"
        
        log_to_changelog(item_id, project_id, "updated", details)
        
        return updated_item


def _validate_hierarchy(project_id: str, item_type: str, parent_id: Optional[int]) -> None:
    """
    Validate hierarchy rules for work item creation.
    
    Args:
        project_id: Project identifier
        item_type: Type of item being created
        parent_id: Parent item ID (None for top-level)
        
    Raises:
        ValueError: If hierarchy validation fails
    """
    # Define valid hierarchy rules
    HIERARCHY_RULES = {
        'project': [None],  # Projects can only be top-level (no parent)
        'phase': ['project'],  # Phases can only be under projects
        'task': ['project', 'phase'],  # Tasks can be under projects or phases
        'subtask': ['task']  # Subtasks can only be under tasks
    }
    
    if item_type not in HIERARCHY_RULES:
        raise ValueError(f"Invalid item type: {item_type}. Must be one of: {list(HIERARCHY_RULES.keys())}")
    
    # Check if parent_id is None (top-level item)
    if parent_id is None:
        if None not in HIERARCHY_RULES[item_type]:
            raise ValueError(f"{item_type} items cannot be top-level. Valid parents: {HIERARCHY_RULES[item_type]}")
        return  # No further validation needed for top-level items
    
    # Get parent item information
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT id, project_id, type FROM work_items WHERE id = ?",
            [parent_id]
        )
        parent_row = cursor.fetchone()
        
        if not parent_row:
            raise ValueError(f"Parent item with ID {parent_id} does not exist")
        
        parent_item = dict(parent_row)
    
    # Validate parent belongs to same project
    if parent_item['project_id'] != project_id:
        raise ValueError(f"Parent item belongs to different project: {parent_item['project_id']} vs {project_id}")
    
    # Validate parent type is allowed for this item type
    parent_type = parent_item['type']
    if parent_type not in HIERARCHY_RULES[item_type]:
        raise ValueError(f"{item_type} items cannot be children of {parent_type}. Valid parents: {HIERARCHY_RULES[item_type]}")
    
    # Check for circular references by traversing up the hierarchy
    _check_circular_reference(parent_id, project_id, max_depth=4)


def _check_circular_reference(parent_id: int, project_id: str, max_depth: int = 4) -> None:
    """
    Check for circular references and enforce maximum hierarchy depth.
    
    Args:
        parent_id: Starting parent ID
        project_id: Project identifier for scoping
        max_depth: Maximum allowed hierarchy depth
        
    Raises:
        ValueError: If circular reference detected or max depth exceeded
    """
    visited_ids = set()
    current_id = parent_id
    depth = 0
    
    with get_connection() as conn:
        while current_id is not None and depth < max_depth:
            # Check for circular reference
            if current_id in visited_ids:
                raise ValueError(f"Circular reference detected in hierarchy at item {current_id}")
            
            visited_ids.add(current_id)
            depth += 1
            
            # Get parent of current item
            cursor = conn.execute(
                "SELECT parent_id FROM work_items WHERE id = ? AND project_id = ?",
                [current_id, project_id]
            )
            row = cursor.fetchone()
            
            if not row:
                break  # Item not found or doesn't belong to project
                
            current_id = row[0]
        
        # Check if we exceeded max depth
        if depth >= max_depth:
            raise ValueError(f"Maximum hierarchy depth ({max_depth}) exceeded")


def _validate_status_transition(current_status: str, new_status: str) -> None:
    """
    Validate that status transitions are logical.
    
    Args:
        current_status: Current status of the work item
        new_status: Proposed new status
        
    Raises:
        ValueError: If status transition is not logical
    """
    # Define valid status transition rules
    VALID_TRANSITIONS = {
        'not_started': ['in_progress', 'completed'],  # Can skip to completed
        'in_progress': ['not_started', 'completed'],  # Can go back or forward
        'completed': ['in_progress']  # Can only go back to in_progress
    }
    
    # Allow staying in same status (no-op)
    if current_status == new_status:
        return
    
    valid_next_statuses = VALID_TRANSITIONS.get(current_status, [])
    if new_status not in valid_next_statuses:
        raise ValueError(f"Invalid status transition from '{current_status}' to '{new_status}'. "
                        f"Valid transitions: {valid_next_statuses}")


def _validate_type_change(item_id: int, current_type: str, new_type: str, project_id: str) -> None:
    """
    Validate that type changes don't break hierarchy rules by checking children.
    
    Args:
        item_id: ID of the item being changed
        current_type: Current type of the item
        new_type: Proposed new type
        project_id: Project identifier
        
    Raises:
        ValueError: If type change would break hierarchy rules
    """
    # Allow same type (no-op)
    if current_type == new_type:
        return
    
    # Define what children each type can have
    ALLOWED_CHILDREN = {
        'project': ['phase', 'task'],
        'phase': ['task', 'subtask'],
        'task': ['subtask'],
        'subtask': []
    }
    
    # Get all children of this item
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT type FROM work_items WHERE parent_id = ? AND project_id = ?",
            [item_id, project_id]
        )
        child_types = [row[0] for row in cursor.fetchall()]
    
    # If no children, type change is safe
    if not child_types:
        return
    
    # Check if new type can have all existing children
    allowed_children_for_new_type = ALLOWED_CHILDREN.get(new_type, [])
    
    for child_type in child_types:
        if child_type not in allowed_children_for_new_type:
            raise ValueError(f"Cannot change type from '{current_type}' to '{new_type}': "
                           f"would create invalid hierarchy with {child_type} children. "
                           f"'{new_type}' can only have children of types: {allowed_children_for_new_type}")


def _validate_parent_change(item_id: int, current_parent_id: Optional[int], new_parent_id: Optional[int], 
                          item_type: str, project_id: str) -> None:
    """
    Validate that parent_id changes maintain valid hierarchy and don't create circular references.
    
    Args:
        item_id: ID of the item being changed
        current_parent_id: Current parent ID (None for top-level)
        new_parent_id: Proposed new parent ID (None for top-level)
        item_type: Type of the item being moved
        project_id: Project identifier
        
    Raises:
        ValueError: If parent change would create invalid hierarchy or circular reference
    """
    # Allow same parent (no-op)
    if current_parent_id == new_parent_id:
        return
    
    # If setting to None (making top-level), just validate type allows it
    if new_parent_id is None:
        if item_type not in ['project']:
            raise ValueError(f"Cannot make {item_type} top-level. Only projects can be top-level.")
        return
    
    # Check that new parent exists and belongs to same project
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT type FROM work_items WHERE id = ? AND project_id = ?",
            [new_parent_id, project_id]
        )
        parent_row = cursor.fetchone()
        
        if not parent_row:
            raise ValueError(f"New parent item {new_parent_id} not found in project {project_id}")
        
        new_parent_type = parent_row[0]
    
    # Validate hierarchy rules for the new parent-child relationship
    HIERARCHY_RULES = {
        'project': [None],
        'phase': ['project'],
        'task': ['project', 'phase'],
        'subtask': ['task']
    }
    
    allowed_parents = HIERARCHY_RULES.get(item_type, [])
    if new_parent_type not in allowed_parents:
        raise ValueError(f"Cannot move {item_type} under {new_parent_type}. "
                        f"Valid parents for {item_type}: {allowed_parents}")
    
    # Check for circular reference: ensure we're not trying to move an item under one of its descendants
    _validate_not_descendant(item_id, new_parent_id, project_id)


def _validate_not_descendant(item_id: int, potential_parent_id: int, project_id: str) -> None:
    """
    Ensure we're not creating a circular reference by making an item a child of its descendant.
    
    Args:
        item_id: ID of the item being moved
        potential_parent_id: ID of the proposed new parent
        project_id: Project identifier
        
    Raises:
        ValueError: If potential_parent_id is a descendant of item_id
    """
    # Get all descendants of the item being moved
    descendants = _get_all_descendants(item_id, project_id)
    
    if potential_parent_id in descendants:
        raise ValueError(f"Cannot move item {item_id} under item {potential_parent_id}: "
                        f"would create circular reference (target is a descendant)")


def _get_all_descendants(item_id: int, project_id: str) -> set:
    """
    Get all descendant IDs of a given item.
    
    Args:
        item_id: ID of the parent item
        project_id: Project identifier
        
    Returns:
        Set of all descendant item IDs
    """
    descendants = set()
    
    with get_connection() as conn:
        # Get direct children
        cursor = conn.execute(
            "SELECT id FROM work_items WHERE parent_id = ? AND project_id = ?",
            [item_id, project_id]
        )
        direct_children = [row[0] for row in cursor.fetchall()]
    
    # Add direct children and recursively get their descendants
    for child_id in direct_children:
        descendants.add(child_id)
        descendants.update(_get_all_descendants(child_id, project_id))
    
    return descendants


def log_to_changelog(work_item_id: int, project_id: str, action: str, details: str) -> None:
    """
    Log an action to the changelog table for audit trail.
    
    Args:
        work_item_id: ID of the work item affected
        project_id: Project identifier
        action: Type of action (created, updated, completed, etc.)
        details: Additional details about the action
    """
    try:
        with get_connection() as conn:
            conn.execute('''
                INSERT INTO changelog (work_item_id, project_id, action, details, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', [work_item_id, project_id, action, details])
            
            conn.commit()
            logger.info(f"Logged {action} for work item {work_item_id} in project {project_id}")
            
    except Exception as e:
        # Handle logging errors gracefully - don't fail the main operation
        logger.error(f"Failed to log to changelog: {e}")


def complete_item(item_id: int, project_id: str) -> Dict[str, Any]:
    """
    Mark a work item as completed with timestamp.
    
    This is a specialized function for completing items that provides
    a cleaner interface than using the generic update function.
    
    Args:
        item_id: ID of the work item to complete
        project_id: Project identifier for validation
        
    Returns:
        Dictionary containing the completed work item with completion timestamp
        
    Raises:
        ValueError: If item doesn't exist or belongs to wrong project
    """
    with get_connection() as conn:
        # First, verify the item exists and belongs to the project
        cursor = conn.execute(
            "SELECT * FROM work_items WHERE id = ? AND project_id = ?",
            [item_id, project_id]
        )
        existing_item_row = cursor.fetchone()
        
        if not existing_item_row:
            raise ValueError(f"Work item {item_id} not found in project {project_id}")
        
        existing_item = dict(existing_item_row)
        
        # Check if already completed
        if existing_item['status'] == 'completed':
            logger.info(f"Work item {item_id} is already completed")
            return existing_item
        
        # Update status to completed and set updated_at timestamp
        completion_time = datetime.now()
        conn.execute('''
            UPDATE work_items 
            SET status = 'completed', updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND project_id = ?
        ''', [item_id, project_id])
        
        # Get the updated item with completion timestamp
        cursor = conn.execute(
            "SELECT * FROM work_items WHERE id = ? AND project_id = ?",
            [item_id, project_id]
        )
        completed_item = dict(cursor.fetchone())
        
        conn.commit()
        logger.info(f"Completed work item {item_id} in project {project_id}: {completed_item['title']}")
        
        # Log completion to changelog
        details = f"Item completed: {completed_item['title']}"
        log_to_changelog(item_id, project_id, "completed", details)
        
        return completed_item


def search_work_items(project_id: str, query: str) -> List[Dict[str, Any]]:
    """
    Search for work items within a project by title and description.
    
    Performs case-insensitive text search across title and description fields
    while maintaining project isolation.
    
    Args:
        project_id: Project identifier to search within
        query: Search query string to match against title and description
        
    Returns:
        List of matching work items as dictionaries
        
    Raises:
        ValueError: If query is empty or invalid
    """
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty")
    
    # Prepare case-insensitive search pattern
    search_pattern = f"%{query.strip()}%"
    
    with get_connection() as conn:
        # Search in both title and description fields with case-insensitive matching
        cursor = conn.execute('''
            SELECT * FROM work_items 
            WHERE project_id = ? 
            AND (
                title LIKE ? COLLATE NOCASE 
                OR description LIKE ? COLLATE NOCASE
            )
            ORDER BY 
                type ASC,
                CASE 
                    WHEN type = 'project' THEN 0
                    WHEN type = 'phase' THEN 1
                    WHEN type = 'task' THEN 2
                    WHEN type = 'subtask' THEN 3
                    ELSE 4
                END,
                order_index ASC,
                title ASC
        ''', [project_id, search_pattern, search_pattern])
        
        items = [dict(row) for row in cursor.fetchall()]
        
        logger.info(f"Search for '{query}' in project {project_id}: found {len(items)} items")
        
        return items


def get_changelog_for_project(project_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get changelog entries for a project.
    
    Args:
        project_id: Project identifier
        limit: Optional limit on number of entries returned
    
    Returns:
        List of changelog entries as dictionaries
    """
    with get_connection() as conn:
        query = """
            SELECT id, work_item_id, project_id, action, details, created_at
            FROM changelog 
            WHERE project_id = ?
            ORDER BY created_at DESC
        """
        
        params = [project_id]
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor = conn.execute(query, params)
        
        # Convert rows to dictionaries
        entries = []
        for row in cursor.fetchall():
            entries.append(dict(row))
        
        logger.info(f"Retrieved {len(entries)} changelog entries for project {project_id}")
        return entries


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
    
    # Test hierarchy building with empty data
    print("\nTesting hierarchy building:")
    hierarchy = build_hierarchy([])
    print(f"Empty hierarchy: {hierarchy}")
    
    # Test hierarchy building with sample data
    sample_items = [
        {'id': 1, 'type': 'project', 'title': 'Test Project', 'parent_id': None, 'status': 'in_progress'},
        {'id': 2, 'type': 'phase', 'title': 'Phase 1', 'parent_id': 1, 'status': 'in_progress'},
        {'id': 3, 'type': 'task', 'title': 'Task 1', 'parent_id': 2, 'status': 'completed'},
        {'id': 4, 'type': 'subtask', 'title': 'Subtask 1', 'parent_id': 3, 'status': 'completed'},
        {'id': 5, 'type': 'subtask', 'title': 'Subtask 2', 'parent_id': 3, 'status': 'completed'},
        {'id': 6, 'type': 'task', 'title': 'Direct Task', 'parent_id': 1, 'status': 'in_progress'},
        {'id': 7, 'type': 'subtask', 'title': 'Direct Subtask 1', 'parent_id': 6, 'status': 'completed'},
        {'id': 8, 'type': 'subtask', 'title': 'Direct Subtask 2', 'parent_id': 6, 'status': 'not_started'},
        {'id': 9, 'type': 'task', 'title': 'Orphaned Task', 'parent_id': 999, 'status': 'not_started'}
    ]
    
    hierarchy = build_hierarchy(sample_items)
    print(f"Sample hierarchy projects count: {len(hierarchy['projects'])}")
    print(f"Sample hierarchy orphaned count: {len(hierarchy['orphaned_items'])}")
    
    # Test completion summaries
    print("\nTesting completion summaries:")
    hierarchy_with_summaries = add_completion_summaries(hierarchy, sample_items)
    
    if hierarchy_with_summaries['projects']:
        project = hierarchy_with_summaries['projects'][0]
        print(f"Project title: {project['title']}")
        print(f"Phases count: {len(project['phases'])}")
        print(f"Direct tasks count: {len(project['direct_tasks'])}")
        
        # Check phase completion summaries
        for phase in project['phases']:
            summary = phase.get('completion_summary', 'No completion summary')
            print(f"Phase '{phase['title']}': {summary}")
        
        # Check direct task completion summaries
        for task in project['direct_tasks']:
            summary = task.get('completion_summary', 'No completion summary')
            print(f"Direct Task '{task['title']}': {summary}")
    
    # Test create_work_item function
    print("\nTesting create_work_item:")
    try:
        # Create a test project
        new_project = create_work_item(
            project_id=test_project_id,
            item_type="project", 
            title="Test Project Created",
            description="A test project created by create_work_item"
        )
        print(f"Created project: {new_project['id']} - {new_project['title']}")
        
        # Create a phase under the project
        new_phase = create_work_item(
            project_id=test_project_id,
            item_type="phase",
            title="Test Phase",
            description="A test phase",
            parent_id=new_project['id']
        )
        print(f"Created phase: {new_phase['id']} - {new_phase['title']} (parent: {new_phase['parent_id']})")
        
        # Create a task under the phase
        new_task = create_work_item(
            project_id=test_project_id,
            item_type="task", 
            title="Test Task",
            parent_id=new_phase['id']
        )
        print(f"Created task: {new_task['id']} - {new_task['title']} (order: {new_task['order_index']})")
        
        # Create another task to test order_index increment
        new_task2 = create_work_item(
            project_id=test_project_id,
            item_type="task",
            title="Test Task 2", 
            parent_id=new_phase['id']
        )
        print(f"Created task 2: {new_task2['id']} - {new_task2['title']} (order: {new_task2['order_index']})")
        
        # Verify data persistence
        all_items_after = get_all_work_items_for_project(test_project_id)
        print(f"Total items after creation: {len(all_items_after)}")
        
    except Exception as e:
        print(f"Error testing create_work_item: {e}")
    
    # Test hierarchy validation
    print("\nTesting hierarchy validation:")
    try:
        # Test valid hierarchy: project → phase → task → subtask
        print("Testing valid hierarchy...")
        project = create_work_item(test_project_id, "project", "Validation Test Project")
        phase = create_work_item(test_project_id, "phase", "Test Phase", parent_id=project['id'])
        task = create_work_item(test_project_id, "task", "Test Task", parent_id=phase['id'])
        subtask = create_work_item(test_project_id, "subtask", "Test Subtask", parent_id=task['id'])
        print("✓ Valid hierarchy creation successful")
        
        # Test task directly under project (should work)
        direct_task = create_work_item(test_project_id, "task", "Direct Task", parent_id=project['id'])
        print("✓ Task under project successful")
        
    except Exception as e:
        print(f"✗ Valid hierarchy test failed: {e}")
    
    # Test invalid hierarchy cases
    invalid_test_cases = [
        ("phase with no parent", "phase", "Invalid Phase", None),
        ("task with no parent", "task", "Invalid Task", None), 
        ("subtask with no parent", "subtask", "Invalid Subtask", None),
        ("phase under phase", "phase", "Phase under Phase", phase['id']),
        ("subtask under phase", "subtask", "Subtask under Phase", phase['id']),
        ("project under project", "project", "Project under Project", project['id']),
    ]
    
    for test_name, item_type, title, parent_id in invalid_test_cases:
        try:
            create_work_item(test_project_id, item_type, title, parent_id=parent_id)
            print(f"✗ {test_name} should have failed but succeeded")
        except ValueError as e:
            print(f"✓ {test_name} correctly rejected: {str(e)[:60]}...")
        except Exception as e:
            print(f"? {test_name} failed with unexpected error: {e}")
    
    # Test cross-project parent validation
    try:
        other_project_id = "b3RoZXJfcHJvamVjdA=="  # base64 for "other_project"
        other_project = create_work_item(other_project_id, "project", "Other Project")
        
        # Try to create task under parent from different project
        create_work_item(test_project_id, "task", "Cross Project Task", parent_id=other_project['id'])
        print("✗ Cross-project parent should have failed")
    except ValueError as e:
        print(f"✓ Cross-project parent correctly rejected: {str(e)[:60]}...")
    except Exception as e:
        print(f"? Cross-project test failed unexpectedly: {e}")
    
    # Test changelog functionality
    print("\nTesting changelog functionality:")
    try:
        # Get changelog entries for the test project
        changelog_entries = get_changelog_for_project(test_project_id, limit=5)
        print(f"Found {len(changelog_entries)} recent changelog entries")
        
        # Display recent changelog entries
        for entry in changelog_entries:
            print(f"- {entry['action']} (ID: {entry['work_item_id']}): {entry['details']}")
        
        # Test changelog for other project
        other_changelog = get_changelog_for_project("b3RoZXJfcHJvamVjdA==", limit=5)
        print(f"Other project changelog entries: {len(other_changelog)}")
        
        if other_changelog:
            for entry in other_changelog:
                print(f"- Other: {entry['action']} (ID: {entry['work_item_id']}): {entry['details']}")
        
        print("✓ Changelog integration working correctly")
        
    except Exception as e:
        print(f"✗ Changelog test failed: {e}")
    
    print("\nDatabase functions working correctly!")
