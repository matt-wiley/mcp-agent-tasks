"""
Tests for hierarchy validation logic - ensuring work item structure integrity.

These tests focus on validating that the hierarchical relationships between
work items are maintained correctly:
- Valid hierarchy creation (project → phase → task → subtask)
- Hierarchy constraint violations
- Circular reference prevention
- Orphaned item handling
"""

import pytest
import sys
from pathlib import Path

# Add the parent directory to Python path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import (
    create_work_item, update_work_item, get_connection,
    build_hierarchy, get_work_items_for_project
)


class TestValidHierarchyCreation:
    """Test creation of valid hierarchical structures."""
    
    def test_full_hierarchy_creation(self, test_db, sample_project_id):
        """Test creating a complete 4-level hierarchy: project → phase → task → subtask."""
        # Create project (level 1)
        project = create_work_item(
            project_id=sample_project_id,
            item_type='project',
            title='Test Project',
            description='Root level project'
        )
        assert project['type'] == 'project'
        assert project['parent_id'] is None
        
        # Create phase under project (level 2)
        phase = create_work_item(
            project_id=sample_project_id,
            item_type='phase',
            title='Test Phase',
            description='Phase under project',
            parent_id=project['id']
        )
        assert phase['type'] == 'phase'
        assert phase['parent_id'] == project['id']
        
        # Create task under phase (level 3)
        task = create_work_item(
            project_id=sample_project_id,
            item_type='task',
            title='Test Task',
            description='Task under phase',
            parent_id=phase['id']
        )
        assert task['type'] == 'task'
        assert task['parent_id'] == phase['id']
        
        # Create subtask under task (level 4)
        subtask = create_work_item(
            project_id=sample_project_id,
            item_type='subtask',
            title='Test Subtask',
            description='Subtask under task',
            parent_id=task['id']
        )
        assert subtask['type'] == 'subtask'
        assert subtask['parent_id'] == task['id']
    
    def test_direct_task_under_project(self, test_db, sample_project_id):
        """Test that tasks can be created directly under projects (valid shortcut)."""
        # Create project
        project = create_work_item(
            project_id=sample_project_id,
            item_type='project',
            title='Test Project'
        )
        
        # Create task directly under project (valid)
        task = create_work_item(
            project_id=sample_project_id,
            item_type='task',
            title='Direct Task',
            parent_id=project['id']
        )
        
        assert task['type'] == 'task'
        assert task['parent_id'] == project['id']
        
        # Create subtask under the direct task
        subtask = create_work_item(
            project_id=sample_project_id,
            item_type='subtask',
            title='Subtask under direct task',
            parent_id=task['id']
        )
        
        assert subtask['type'] == 'subtask'
        assert subtask['parent_id'] == task['id']
    
    def test_multiple_children_same_parent(self, test_db, sample_project_id):
        """Test that multiple items can share the same parent."""
        # Create project
        project = create_work_item(
            project_id=sample_project_id,
            item_type='project',
            title='Test Project'
        )
        
        # Create multiple phases under the same project
        phase1 = create_work_item(
            project_id=sample_project_id,
            item_type='phase',
            title='Phase 1',
            parent_id=project['id']
        )
        
        phase2 = create_work_item(
            project_id=sample_project_id,
            item_type='phase',
            title='Phase 2',
            parent_id=project['id']
        )
        
        phase3 = create_work_item(
            project_id=sample_project_id,
            item_type='phase',
            title='Phase 3',
            parent_id=project['id']
        )
        
        assert phase1['parent_id'] == project['id']
        assert phase2['parent_id'] == project['id']
        assert phase3['parent_id'] == project['id']
        
        # Verify all phases exist and have correct ordering
        phases = [phase1, phase2, phase3]
        for i, phase in enumerate(phases, 1):
            assert phase['title'] == f'Phase {i}'
            assert phase['order_index'] == i * 10.0  # Should auto-increment by 10


class TestHierarchyConstraintViolations:
    """Test that invalid hierarchy relationships are properly rejected."""
    
    def test_subtask_cannot_have_children(self, test_db, sample_project_id):
        """Test that subtasks cannot have children (deepest level)."""
        # Create valid hierarchy to subtask level
        project = create_work_item(
            project_id=sample_project_id,
            item_type='project',
            title='Test Project'
        )
        
        task = create_work_item(
            project_id=sample_project_id,
            item_type='task',
            title='Test Task',
            parent_id=project['id']
        )
        
        subtask = create_work_item(
            project_id=sample_project_id,
            item_type='subtask',
            title='Test Subtask',
            parent_id=task['id']
        )
        
        # Try to create any item under subtask (should fail)
        with pytest.raises(ValueError, match="subtask items cannot be children of subtask"):
            create_work_item(
                project_id=sample_project_id,
                item_type='subtask',
                title='Invalid Child',
                parent_id=subtask['id']
            )
    
    def test_invalid_parent_child_combinations(self, test_db, sample_project_id):
        """Test various invalid parent-child type combinations."""
        # Create base items for testing
        project = create_work_item(
            project_id=sample_project_id,
            item_type='project',
            title='Test Project'
        )
        
        phase = create_work_item(
            project_id=sample_project_id,
            item_type='phase',
            title='Test Phase',
            parent_id=project['id']
        )
        
        task = create_work_item(
            project_id=sample_project_id,
            item_type='task',
            title='Test Task',
            parent_id=phase['id']
        )
        
        # Test invalid combinations
        
        # 1. Subtask directly under project (should fail)
        with pytest.raises(ValueError, match="subtask items cannot be children of project"):
            create_work_item(
                project_id=sample_project_id,
                item_type='subtask',
                title='Invalid Subtask',
                parent_id=project['id']
            )
        
        # 2. Subtask directly under phase (should fail)
        with pytest.raises(ValueError, match="subtask items cannot be children of phase"):
            create_work_item(
                project_id=sample_project_id,
                item_type='subtask',
                title='Invalid Subtask',
                parent_id=phase['id']
            )
        
        # 3. Phase under task (should fail - phases are higher level)
        with pytest.raises(ValueError, match="phase items cannot be children of task"):
            create_work_item(
                project_id=sample_project_id,
                item_type='phase',
                title='Invalid Phase',
                parent_id=task['id']
            )
        
        # 4. Phase under subtask (should fail)
        subtask = create_work_item(
            project_id=sample_project_id,
            item_type='subtask',
            title='Test Subtask',
            parent_id=task['id']
        )
        
        with pytest.raises(ValueError, match="phase items cannot be children of subtask"):
            create_work_item(
                project_id=sample_project_id,
                item_type='phase',
                title='Invalid Phase',
                parent_id=subtask['id']
            )
    
    def test_project_cannot_have_parent(self, test_db, sample_project_id):
        """Test that projects cannot have parents (must be root level)."""
        # Create a project first
        project1 = create_work_item(
            project_id=sample_project_id,
            item_type='project',
            title='Test Project 1'
        )
        
        # Try to create another project with the first as parent (should fail)
        with pytest.raises(ValueError, match="project items cannot be children of project"):
            create_work_item(
                project_id=sample_project_id,
                item_type='project',
                title='Invalid Child Project',
                parent_id=project1['id']
            )
    
    def test_orphaned_items_validation(self, test_db, sample_project_id):
        """Test that items requiring parents are validated."""
        # Test phase without parent
        with pytest.raises(ValueError, match="phase items cannot be top-level"):
            create_work_item(
                project_id=sample_project_id,
                item_type='phase',
                title='Orphaned Phase'
                # No parent_id provided
            )
        
        # Test task without parent
        with pytest.raises(ValueError, match="task items cannot be top-level"):
            create_work_item(
                project_id=sample_project_id,
                item_type='task',
                title='Orphaned Task'
                # No parent_id provided
            )
        
        # Test subtask without parent
        with pytest.raises(ValueError, match="subtask items cannot be top-level"):
            create_work_item(
                project_id=sample_project_id,
                item_type='subtask',
                title='Orphaned Subtask'
                # No parent_id provided
            )


class TestCircularReferencesPrevention:
    """Test prevention of circular references in hierarchy."""
    
    def test_cannot_make_item_its_own_parent(self, test_db, sample_project_id):
        """Test that an item cannot be updated to have itself as parent."""
        # Create a task
        project = create_work_item(
            project_id=sample_project_id,
            item_type='project',
            title='Test Project'
        )
        
        task = create_work_item(
            project_id=sample_project_id,
            item_type='task',
            title='Test Task',
            parent_id=project['id']
        )
        
        # Try to make task its own parent
        with pytest.raises(ValueError, match="Cannot move task under task"):
            update_work_item(
                item_id=task['id'],
                project_id=sample_project_id,
                parent_id=task['id']
            )
    
    def test_cannot_create_circular_reference_chain(self, test_db, sample_project_id):
        """Test that circular reference chains are prevented."""
        # Create hierarchy: project → phase → task
        project = create_work_item(
            project_id=sample_project_id,
            item_type='project',
            title='Test Project'
        )
        
        phase = create_work_item(
            project_id=sample_project_id,
            item_type='phase',
            title='Test Phase',
            parent_id=project['id']
        )
        
        task = create_work_item(
            project_id=sample_project_id,
            item_type='task',
            title='Test Task',
            parent_id=phase['id']
        )
        
        # Try to make project the child of task (would create cycle)
        with pytest.raises(ValueError, match="Cannot move project under task"):
            update_work_item(
                item_id=project['id'],
                project_id=sample_project_id,
                parent_id=task['id']
            )
        
        # Try to make phase the child of task (would create cycle)
        with pytest.raises(ValueError, match="Cannot move phase under task"):
            update_work_item(
                item_id=phase['id'],
                project_id=sample_project_id,
                parent_id=task['id']
            )
    
    def test_deep_hierarchy_depth_limit(self, test_db, sample_project_id):
        """Test that hierarchy depth is limited to prevent excessive nesting."""
        # Create maximum valid depth: project → phase → task → subtask (4 levels)
        project = create_work_item(
            project_id=sample_project_id,
            item_type='project',
            title='Test Project'
        )
        
        phase = create_work_item(
            project_id=sample_project_id,
            item_type='phase',
            title='Test Phase',
            parent_id=project['id']
        )
        
        task = create_work_item(
            project_id=sample_project_id,
            item_type='task',
            title='Test Task',
            parent_id=phase['id']
        )
        
        subtask = create_work_item(
            project_id=sample_project_id,
            item_type='subtask',
            title='Test Subtask',
            parent_id=task['id']
        )
        
        # This should succeed (4 levels is maximum)
        assert subtask['parent_id'] == task['id']
        
        # Verify we can't go deeper (subtasks can't have children)
        with pytest.raises(ValueError, match="subtask items cannot be children of subtask"):
            create_work_item(
                project_id=sample_project_id,
                item_type='subtask',
                title='Too Deep Subtask',
                parent_id=subtask['id']
            )


class TestOrphanedItemHandling:
    """Test handling of orphaned items and hierarchy integrity."""
    
    def test_orphaned_items_in_hierarchy_building(self, test_db, sample_project_id):
        """Test that orphaned items are handled properly in hierarchy building."""
        # Create valid hierarchy
        project = create_work_item(
            project_id=sample_project_id,
            item_type='project',
            title='Test Project'
        )
        
        task = create_work_item(
            project_id=sample_project_id,
            item_type='task',
            title='Valid Task',
            parent_id=project['id']
        )
        
        # Manually insert an orphaned item (parent_id points to non-existent item)
        with get_connection() as conn:
            conn.execute('''
                INSERT INTO work_items (
                    project_id, type, title, description, status, parent_id, 
                    order_index, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', [
                sample_project_id, 'task', 'Orphaned Task', 'Has invalid parent', 
                'not_started', 99999, 1.0  # parent_id 99999 doesn't exist
            ])
            conn.commit()
        
        # Get all items and build hierarchy
        all_items = get_work_items_for_project(sample_project_id)
        hierarchy = build_hierarchy(all_items)
        
        # Should have orphaned items section
        assert 'orphaned_items' in hierarchy
        assert len(hierarchy['orphaned_items']) == 1
        assert hierarchy['orphaned_items'][0]['title'] == 'Orphaned Task'
        
        # Valid items should still be in proper hierarchy
        assert len(hierarchy['projects']) == 1
        assert hierarchy['projects'][0]['title'] == 'Test Project'
    
    def test_parent_belongs_to_same_project(self, test_db, sample_project_id):
        """Test that parent items must belong to the same project."""
        # Create project in first project_id
        project1 = create_work_item(
            project_id=sample_project_id,
            item_type='project',
            title='Project 1'
        )
        
        # Create project in second project_id
        from project_id import get_project_id
        other_project_id = get_project_id("different_project_path")['project_id']
        project2 = create_work_item(
            project_id=other_project_id,
            item_type='project',
            title='Project 2'
        )
        
        # Try to create task in project1 with parent from project2 (should fail)
        with pytest.raises(ValueError, match="Parent item belongs to different project"):
            create_work_item(
                project_id=sample_project_id,
                item_type='task',
                title='Cross-project task',
                parent_id=project2['id']  # Parent from different project
            )
    
    def test_valid_parent_exists(self, test_db, sample_project_id):
        """Test that parent_id must reference an existing item."""
        # Try to create item with non-existent parent_id
        with pytest.raises(ValueError, match="Parent item with ID .* does not exist"):
            create_work_item(
                project_id=sample_project_id,
                item_type='task',
                title='Task with bad parent',
                parent_id=99999  # Non-existent ID
            )


class TestHierarchyUpdateValidation:
    """Test validation when updating hierarchy relationships."""
    
    def test_valid_hierarchy_updates(self, test_db, sample_project_id):
        """Test that valid hierarchy updates work correctly."""
        # Create initial hierarchy
        project = create_work_item(
            project_id=sample_project_id,
            item_type='project',
            title='Test Project'
        )
        
        phase1 = create_work_item(
            project_id=sample_project_id,
            item_type='phase',
            title='Phase 1',
            parent_id=project['id']
        )
        
        phase2 = create_work_item(
            project_id=sample_project_id,
            item_type='phase',
            title='Phase 2',
            parent_id=project['id']
        )
        
        task = create_work_item(
            project_id=sample_project_id,
            item_type='task',
            title='Test Task',
            parent_id=phase1['id']
        )
        
        # Move task from phase1 to phase2 (valid)
        updated_task = update_work_item(
            item_id=task['id'],
            project_id=sample_project_id,
            parent_id=phase2['id']
        )
        
        assert updated_task['parent_id'] == phase2['id']
    
    def test_invalid_hierarchy_updates_rejected(self, test_db, sample_project_id):
        """Test that invalid hierarchy updates are rejected."""
        # Create hierarchy
        project = create_work_item(
            project_id=sample_project_id,
            item_type='project',
            title='Test Project'
        )
        
        task = create_work_item(
            project_id=sample_project_id,
            item_type='task',
            title='Test Task',
            parent_id=project['id']
        )
        
        subtask = create_work_item(
            project_id=sample_project_id,
            item_type='subtask',
            title='Test Subtask',
            parent_id=task['id']
        )
        
        # Try to make project a child of subtask (invalid hierarchy)
        with pytest.raises(ValueError, match="Cannot move project under subtask"):
            update_work_item(
                item_id=project['id'],
                project_id=sample_project_id,
                parent_id=subtask['id']
            )
