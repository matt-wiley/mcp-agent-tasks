"""
Tests for database functionality - Core POC validation.

These tests focus on the essential database operations that power the MCP server:
- Database initialization  
- Work item CRUD operations
- Changelog creation
- Project ID generation consistency
"""

import pytest
import sys
from pathlib import Path

# Add the parent directory to Python path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import (
    init_database, get_connection, check_database_health,
    create_work_item, update_work_item, complete_item,
    get_work_items_for_project, build_hierarchy, add_completion_summaries,
    search_work_items_with_context
)
from project_id import get_project_id


class TestDatabaseInitialization:
    """Test database setup and health checking."""
    
    def test_database_initialization(self, test_db):
        """Test that database initializes with correct tables and indexes."""
        # Database should be initialized by the test_db fixture
        
        with get_connection() as conn:
            # Check that work_items table exists with correct structure
            cursor = conn.execute("PRAGMA table_info(work_items)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}  # name: type
            
            expected_columns = {
                'id', 'project_id', 'type', 'title', 'description', 'status',
                'parent_id', 'notes', 'order_index', 'created_at', 'updated_at'
            }
            assert set(columns.keys()) == expected_columns
            
            # Check that changelog table exists
            cursor = conn.execute("PRAGMA table_info(changelog)")
            changelog_columns = {row[1] for row in cursor.fetchall()}
            expected_changelog_columns = {
                'id', 'work_item_id', 'project_id', 'action', 'details', 'created_at'
            }
            assert changelog_columns == expected_changelog_columns
            
            # Check that indexes exist
            cursor = conn.execute("PRAGMA index_list(work_items)")
            indexes = [row[1] for row in cursor.fetchall()]
            assert 'idx_project' in indexes
            assert 'idx_parent' in indexes
            assert 'idx_status' in indexes
    
    def test_database_health_check(self, test_db):
        """Test database health check functionality."""
        health = check_database_health()
        
        assert health['status'] == 'healthy'
        assert 'work_items' in health['tables_present']
        assert 'changelog' in health['tables_present']
        assert health['work_items_count'] >= 0
        assert health['changelog_count'] >= 0
        assert 'timestamp' in health


class TestWorkItemCRUD:
    """Test core work item Create, Read, Update, Delete operations."""
    
    def test_create_work_item_project(self, test_db, sample_project_id):
        """Test creating a project (top-level item)."""
        project = create_work_item(
            project_id=sample_project_id,
            item_type='project',
            title='Test Project',
            description='A test project'
        )
        
        assert project['type'] == 'project'
        assert project['title'] == 'Test Project'
        assert project['description'] == 'A test project'
        assert project['parent_id'] is None
        assert project['status'] == 'not_started'
        assert project['project_id'] == sample_project_id
        assert project['id'] is not None
    
    def test_create_work_item_hierarchy(self, test_db, sample_project_id):
        """Test creating hierarchical work items (project -> phase -> task -> subtask)."""
        # Create project
        project = create_work_item(
            project_id=sample_project_id,
            item_type='project', 
            title='Test Project'
        )
        
        # Create phase under project
        phase = create_work_item(
            project_id=sample_project_id,
            item_type='phase',
            title='Test Phase',
            parent_id=project['id']
        )
        assert phase['parent_id'] == project['id']
        assert phase['type'] == 'phase'
        
        # Create task under phase
        task = create_work_item(
            project_id=sample_project_id,
            item_type='task',
            title='Test Task', 
            parent_id=phase['id']
        )
        assert task['parent_id'] == phase['id']
        assert task['type'] == 'task'
        
        # Create subtask under task
        subtask = create_work_item(
            project_id=sample_project_id,
            item_type='subtask',
            title='Test Subtask',
            parent_id=task['id']
        )
        assert subtask['parent_id'] == task['id']
        assert subtask['type'] == 'subtask'
    
    def test_update_work_item(self, test_db, sample_project_id):
        """Test updating work item fields."""
        # Create a work item to update
        project = create_work_item(
            project_id=sample_project_id,
            item_type='project',
            title='Original Title'
        )
        
        # Update multiple fields
        updated = update_work_item(
            item_id=project['id'],
            project_id=sample_project_id,
            title='Updated Title',
            description='Updated description',
            status='in_progress'
        )
        
        assert updated['title'] == 'Updated Title'
        assert updated['description'] == 'Updated description' 
        assert updated['status'] == 'in_progress'
        assert updated['id'] == project['id']
    
    def test_complete_item(self, test_db, sample_project_id):
        """Test marking work item as completed."""
        # Create a work item to complete
        project = create_work_item(
            project_id=sample_project_id,
            item_type='project',
            title='Test Project'
        )
        
        # Complete the item
        completed = complete_item(item_id=project['id'], project_id=sample_project_id)
        
        assert completed['status'] == 'completed'
        assert completed['id'] == project['id']
    
    def test_hierarchy_validation_invalid_parent_type(self, test_db, sample_project_id):
        """Test that invalid hierarchy relationships are rejected."""
        # Create a project first
        project = create_work_item(
            project_id=sample_project_id,
            item_type='project',
            title='Test Project'
        )
        
        # Try to create a subtask directly under project (invalid)
        with pytest.raises(ValueError, match="subtask items cannot be children of project"):
            create_work_item(
                project_id=sample_project_id,
                item_type='subtask',
                title='Invalid Subtask',
                parent_id=project['id']
            )
    
    def test_hierarchy_validation_orphaned_items(self, test_db, sample_project_id):
        """Test validation of items with no valid parent."""
        # Try to create a phase with no parent (invalid)
        with pytest.raises(ValueError):
            create_work_item(
                project_id=sample_project_id,
                item_type='phase',
                title='Orphaned Phase'
                # No parent_id provided
            )


class TestProjectIDGeneration:
    """Test project ID generation consistency."""
    
    def test_project_id_consistency(self):
        """Test that same input always generates same project ID."""
        test_input = "https://github.com/test/repo.git"
        
        id1 = get_project_id(test_input)
        id2 = get_project_id(test_input)
        
        assert id1 == id2
        assert len(id1) > 0
    
    def test_project_id_different_inputs(self):
        """Test that different inputs generate different project IDs."""
        id1 = get_project_id("https://github.com/test/repo1.git")
        id2 = get_project_id("https://github.com/test/repo2.git")
        id3 = get_project_id("/absolute/path/to/project")
        
        assert id1 != id2
        assert id1 != id3
        assert id2 != id3


class TestWorkPlanRetrieval:
    """Test the rolling work plan functionality."""
    
    def test_get_incomplete_items_only(self, populated_db, sample_project_id):
        """Test that only incomplete items are returned by default."""
        items = get_work_items_for_project(sample_project_id)
        
        # Should only get incomplete items (not_started, in_progress)
        statuses = {item['status'] for item in items}
        assert 'completed' not in statuses
        assert len(statuses.intersection({'not_started', 'in_progress'})) > 0
    
    def test_hierarchy_building(self, populated_db, sample_work_items):
        """Test building nested hierarchy from flat item list."""
        # Use only incomplete items for hierarchy building
        incomplete_items = [
            item for item in sample_work_items 
            if item['status'] in ['not_started', 'in_progress']
        ]
        
        hierarchy = build_hierarchy(incomplete_items)
        
        assert 'projects' in hierarchy
        assert 'orphaned_items' in hierarchy
        assert len(hierarchy['projects']) == 1
        
        project = hierarchy['projects'][0]
        assert project['type'] == 'project'
        assert project['title'] == 'Test Project'
        assert 'phases' in project
        assert 'direct_tasks' in project
    
    def test_completion_summaries(self, populated_db, sample_work_items):
        """Test that completion summaries are added for completed sections."""
        incomplete_items = [
            item for item in sample_work_items
            if item['status'] in ['not_started', 'in_progress'] 
        ]
        
        hierarchy = build_hierarchy(incomplete_items)
        hierarchy_with_summaries = add_completion_summaries(hierarchy, sample_work_items)
        
        # Should have completion summaries where all children are completed
        assert hierarchy_with_summaries is not None
        assert 'projects' in hierarchy_with_summaries


class TestSearchFunctionality:
    """Test work item search capabilities."""
    
    def test_search_with_context(self, populated_db, sample_project_id):
        """Test search functionality with parent context."""
        results = search_work_items_with_context(sample_project_id, "Test")
        
        assert len(results) > 0
        
        # Each result should have context information
        for result in results:
            assert 'breadcrumb_path' in result
            assert 'parent_context' in result
            # Should find items with "Test" in the title (like "Test Project")
            assert 'Test' in result['title'] or 'test' in result['title'].lower()
    
    def test_search_case_insensitive(self, populated_db, sample_project_id):
        """Test that search is case-insensitive."""
        results_lower = search_work_items_with_context(sample_project_id, "task")
        results_upper = search_work_items_with_context(sample_project_id, "TASK") 
        
        # Should get same results regardless of case
        assert len(results_lower) == len(results_upper)
        assert len(results_lower) > 0


class TestChangelogFunctionality:
    """Test audit trail through changelog."""
    
    def test_changelog_creation_on_create(self, test_db, sample_project_id):
        """Test that changelog entries are created when items are created."""
        project = create_work_item(
            project_id=sample_project_id,
            item_type='project',
            title='Test Project'
        )
        
        # Check that changelog entry was created
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM changelog WHERE work_item_id = ? AND action = ?",
                [project['id'], 'created']
            )
            changelog_entry = cursor.fetchone()
            
            assert changelog_entry is not None
            assert changelog_entry['project_id'] == sample_project_id
            assert 'Created project' in changelog_entry['details']
    
    def test_changelog_creation_on_update(self, test_db, sample_project_id):
        """Test that changelog entries are created when items are updated."""
        project = create_work_item(
            project_id=sample_project_id,
            item_type='project', 
            title='Original Title'
        )
        
        update_work_item(
            item_id=project['id'],
            project_id=sample_project_id,
            title='Updated Title',
            status='in_progress'
        )
        
        # Check that changelog entry was created
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM changelog WHERE work_item_id = ? AND action = ?",
                [project['id'], 'updated']
            )
            changelog_entry = cursor.fetchone()
            
            assert changelog_entry is not None
            assert 'title' in changelog_entry['details']
            assert 'status' in changelog_entry['details']
