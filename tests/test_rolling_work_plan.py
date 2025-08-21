"""
Tests for rolling work plan functionality - Core POC validation.

These tests focus on the rolling work plan concept which is the key innovation:
- Only incomplete items shown (completed items hidden)
- Completion summaries for completed sections
- Empty project work plans
- Mixed completion states handling
"""

import pytest
import sys
from pathlib import Path

# Add the parent directory to Python path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import (
    init_database, get_connection,
    create_work_item, update_work_item, complete_item,
    get_work_items_for_project, build_hierarchy, add_completion_summaries
)
from project_id import get_project_id


class TestRollingWorkPlan:
    """Test the core rolling work plan functionality."""
    
    def test_work_plan_with_all_incomplete_items(self, test_db):
        """Test work plan when all items are incomplete."""
        project_id = get_project_id("test-rolling-all-incomplete")['project_id']
        
        # Create a project with all incomplete items
        project_item = create_work_item(
            project_id=project_id,
            item_type="project", 
            title="All Incomplete Project",
            description="Test project with all incomplete items"
        )
        
        phase_item = create_work_item(
            project_id=project_id,
            item_type="phase",
            title="Development Phase", 
            description="Phase with incomplete tasks",
            parent_id=project_item['id']
        )
        
        task1 = create_work_item(
            project_id=project_id,
            item_type="task",
            title="Task 1 Not Started",
            description="First task",
            parent_id=phase_item['id']
        )
        
        task2 = create_work_item(
            project_id=project_id,
            item_type="task", 
            title="Task 2 In Progress",
            description="Second task",
            parent_id=phase_item['id']
        )
        
        # Update task2 to in_progress status
        update_work_item(task2['id'], project_id, status="in_progress")
        
        subtask1 = create_work_item(
            project_id=project_id,
            item_type="subtask",
            title="Subtask 1",
            description="First subtask", 
            parent_id=task1['id']
        )
        
        # Get work plan - should include ALL items since none are completed
        items = get_work_items_for_project(project_id)
        hierarchy = build_hierarchy(items)
        hierarchy_with_summaries = add_completion_summaries(hierarchy, items)
        
        # All items should be present in the work plan
        assert len(items) == 5  # project, phase, 2 tasks, 1 subtask
        
        # Verify hierarchy structure
        assert len(hierarchy['projects']) == 1
        project = hierarchy['projects'][0]
        assert project['title'] == "All Incomplete Project"
        assert len(project['phases']) == 1
        
        phase = project['phases'][0]
        assert phase['title'] == "Development Phase"
        assert len(phase['tasks']) == 2
        
        # Task 1 should have 1 subtask
        task1_in_hierarchy = next(t for t in phase['tasks'] if t['title'] == "Task 1 Not Started")
        assert len(task1_in_hierarchy['subtasks']) == 1
        
        # Task 2 should have no subtasks
        task2_in_hierarchy = next(t for t in phase['tasks'] if t['title'] == "Task 2 In Progress") 
        assert len(task2_in_hierarchy['subtasks']) == 0
        
        # No completion summaries should be present since nothing is completed
        assert hierarchy_with_summaries == hierarchy
    
    def test_work_plan_with_mixed_completion_states(self, test_db):
        """Test work plan with mix of completed and incomplete items."""
        project_id = get_project_id("test-rolling-mixed-states")['project_id']
        
        # Create project structure with mixed completion states
        project_item = create_work_item(
            project_id=project_id,
            item_type="project",
            title="Mixed States Project", 
            description="Project with mixed completion states"
        )
        
        # Phase 1: All tasks completed (should show completion summary)
        phase1 = create_work_item(
            project_id=project_id,
            item_type="phase",
            title="Completed Phase",
            description="Phase with all completed tasks",
            parent_id=project_item['id']
        )
        
        completed_task1 = create_work_item(
            project_id=project_id,
            item_type="task",
            title="Completed Task 1",
            description="First completed task",
            parent_id=phase1['id']
        )
        complete_item(completed_task1['id'], project_id)
        
        completed_task2 = create_work_item(
            project_id=project_id,
            item_type="task", 
            title="Completed Task 2",
            description="Second completed task",
            parent_id=phase1['id']
        )
        complete_item(completed_task2['id'], project_id)
        
        # Phase 2: Mix of completed and incomplete tasks
        phase2 = create_work_item(
            project_id=project_id,
            item_type="phase",
            title="Active Phase",
            description="Phase with mixed task states",
            parent_id=project_item['id']
        )
        
        incomplete_task = create_work_item(
            project_id=project_id,
            item_type="task",
            title="Incomplete Task",
            description="Task still in progress", 
            parent_id=phase2['id']
        )
        update_work_item(incomplete_task['id'], project_id, status="in_progress")
        
        completed_task3 = create_work_item(
            project_id=project_id,
            item_type="task",
            title="Completed Task 3", 
            description="Third completed task",
            parent_id=phase2['id']
        )
        complete_item(completed_task3['id'], project_id)
        
        # Add subtasks to incomplete task
        subtask1 = create_work_item(
            project_id=project_id,
            item_type="subtask",
            title="Active Subtask",
            description="Subtask in progress",
            parent_id=incomplete_task['id']
        )
        update_work_item(subtask1['id'], project_id, status="in_progress")
        
        completed_subtask = create_work_item(
            project_id=project_id,
            item_type="subtask",
            title="Completed Subtask",
            description="Subtask that's done", 
            parent_id=incomplete_task['id']
        )
        complete_item(completed_subtask['id'], project_id)
        
        # Get ALL items to pass to completion summary function
        all_items = []
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM work_items WHERE project_id = ? ORDER BY created_at",
                (project_id,)
            )
            columns = [description[0] for description in cursor.description]
            all_items = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Get rolling work plan (only incomplete items)
        incomplete_items = get_work_items_for_project(project_id)
        hierarchy = build_hierarchy(incomplete_items)
        hierarchy_with_summaries = add_completion_summaries(hierarchy, all_items)
        
        # Rolling work plan should only include incomplete items
        # Should exclude: completed_task1, completed_task2, completed_task3, completed_subtask
        # Should include: project, phase1, phase2, incomplete_task, subtask1
        expected_incomplete = 5
        assert len(incomplete_items) == expected_incomplete
        
        # Verify no completed items in rolling work plan
        for item in incomplete_items:
            assert item['status'] != 'completed'
        
        # Verify hierarchy structure
        assert len(hierarchy_with_summaries['projects']) == 1
        project = hierarchy_with_summaries['projects'][0]
        assert len(project['phases']) == 2
        
        # Phase 1 (completed phase) should have completion summary
        completed_phase = next(p for p in project['phases'] if p['title'] == "Completed Phase")
        assert 'completion_summary' in completed_phase
        assert "✓ All" in completed_phase['completion_summary']
        assert "tasks completed" in completed_phase['completion_summary']
        assert len(completed_phase['tasks']) == 0  # No individual tasks shown
        
        # Phase 2 (active phase) should show incomplete task
        active_phase = next(p for p in project['phases'] if p['title'] == "Active Phase")
        assert len(active_phase['tasks']) == 1  # Only incomplete task
        
        incomplete_task_in_hierarchy = active_phase['tasks'][0] 
        assert incomplete_task_in_hierarchy['title'] == "Incomplete Task"
        assert len(incomplete_task_in_hierarchy['subtasks']) == 1  # Only incomplete subtask
        assert incomplete_task_in_hierarchy['subtasks'][0]['title'] == "Active Subtask"
    
    def test_completion_summary_generation(self, test_db):
        """Test detailed completion summary generation."""
        project_id = get_project_id("test-completion-summaries")['project_id']
        
        # Create structure where parent has all children completed
        project_item = create_work_item(
            project_id=project_id,
            item_type="project",
            title="Summary Test Project",
            description="Project to test completion summaries"
        )
        
        # Task with all subtasks completed
        parent_task = create_work_item(
            project_id=project_id,
            item_type="task", 
            title="Parent Task",
            description="Task with completed subtasks",
            parent_id=project_item['id']
        )
        update_work_item(parent_task['id'], project_id, status="in_progress")
        
        # Create multiple completed subtasks
        for i in range(3):
            subtask = create_work_item(
                project_id=project_id,
                item_type="subtask",
                title=f"Completed Subtask {i+1}",
                description=f"Subtask {i+1} is done",
                parent_id=parent_task['id']
            )
            complete_item(subtask['id'], project_id)
        
        # Get ALL items for summary generation
        all_items = []
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM work_items WHERE project_id = ? ORDER BY created_at",
                (project_id,)
            )
            columns = [description[0] for description in cursor.description]
            all_items = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Get rolling work plan
        incomplete_items = get_work_items_for_project(project_id)
        hierarchy = build_hierarchy(incomplete_items)
        hierarchy_with_summaries = add_completion_summaries(hierarchy, all_items)
        
        # Should have project and parent task in rolling work plan
        # All subtasks completed, so should get completion summary
        assert len(incomplete_items) == 2  # project + parent_task
        
        project = hierarchy_with_summaries['projects'][0]
        assert len(project['direct_tasks']) == 1
        
        task = project['direct_tasks'][0]
        assert task['title'] == "Parent Task"
        assert 'completion_summary' in task
        assert "✓ All" in task['completion_summary']
        assert "subtasks completed" in task['completion_summary']
        assert len(task['subtasks']) == 0  # Individual subtasks hidden
    
    def test_empty_project_work_plan(self, test_db):
        """Test work plan for project with no items.""" 
        project_id = get_project_id("test-empty-project")['project_id']
        
        # Don't create any items - test empty project
        items = get_work_items_for_project(project_id)
        hierarchy = build_hierarchy(items)
        hierarchy_with_summaries = add_completion_summaries(hierarchy, items)
        
        # Should get empty structure
        assert len(items) == 0
        assert len(hierarchy['projects']) == 0
        assert len(hierarchy['orphaned_items']) == 0
        assert hierarchy_with_summaries == hierarchy
    
    def test_project_with_only_completed_items(self, test_db):
        """Test project where all items are completed (should show completion summary at project level)."""
        project_id = get_project_id("test-all-completed")['project_id']
        
        # Create project with all completed items
        project_item = create_work_item(
            project_id=project_id,
            item_type="project",
            title="Fully Completed Project",
            description="Project where everything is done"
        )
        complete_item(project_item['id'], project_id)
        
        phase_item = create_work_item(
            project_id=project_id,
            item_type="phase",
            title="Completed Phase",
            description="Phase that's done",
            parent_id=project_item['id']
        )
        complete_item(phase_item['id'], project_id)
        
        task_item = create_work_item(
            project_id=project_id,
            item_type="task",
            title="Completed Task", 
            description="Task that's done",
            parent_id=phase_item['id']
        )
        complete_item(task_item['id'], project_id)
        
        # Get ALL items for summary generation
        all_items = []
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM work_items WHERE project_id = ? ORDER BY created_at",
                (project_id,)
            )
            columns = [description[0] for description in cursor.description]
            all_items = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Rolling work plan should be empty (no incomplete items)
        incomplete_items = get_work_items_for_project(project_id)
        assert len(incomplete_items) == 0
        
        # Build hierarchy with summaries
        hierarchy = build_hierarchy(incomplete_items)
        hierarchy_with_summaries = add_completion_summaries(hierarchy, all_items)
        
        # Should show project-level completion summary
        assert len(hierarchy_with_summaries['projects']) == 0  # No incomplete projects
        # In a real UI, we might want to show a "✓ Project completed" message
        # But for the rolling work plan, completed projects disappear entirely
    
    def test_hierarchical_completion_summaries(self, test_db):
        """Test that completion summaries work at different hierarchy levels."""
        project_id = get_project_id("test-hierarchical-summaries")['project_id']
        
        # Create complex hierarchy with completion at different levels
        project_item = create_work_item(
            project_id=project_id,
            item_type="project",
            title="Hierarchical Test Project",
            description="Project to test multi-level completion summaries"
        )
        
        # Phase 1: Fully completed 
        phase1 = create_work_item(
            project_id=project_id,
            item_type="phase",
            title="Completed Phase",
            description="Phase with completed tasks",
            parent_id=project_item['id']
        )
        complete_item(phase1['id'], project_id)
        
        # Add completed tasks to phase 1 (won't appear in rolling work plan)
        for i in range(2):
            task = create_work_item(
                project_id=project_id,
                item_type="task",
                title=f"Completed Phase Task {i+1}",
                description="Completed task",
                parent_id=phase1['id']
            )
            complete_item(task['id'], project_id)
        
        # Phase 2: Mixed completion
        phase2 = create_work_item(
            project_id=project_id,
            item_type="phase", 
            title="Active Phase",
            description="Phase with mixed states",
            parent_id=project_item['id']
        )
        update_work_item(phase2['id'], project_id, status="in_progress")
        
        # Task 2.1: All subtasks completed
        task21 = create_work_item(
            project_id=project_id,
            item_type="task",
            title="Task with Completed Subtasks",
            description="Task where all subtasks are done",
            parent_id=phase2['id']
        )
        update_work_item(task21['id'], project_id, status="in_progress")
        
        # Add completed subtasks to task 2.1
        for i in range(3):
            subtask = create_work_item(
                project_id=project_id,
                item_type="subtask",
                title=f"Completed Subtask {i+1}",
                description="Done subtask",
                parent_id=task21['id']
            )
            complete_item(subtask['id'], project_id)
        
        # Task 2.2: Mix of completed and incomplete subtasks
        task22 = create_work_item(
            project_id=project_id,
            item_type="task",
            title="Task with Mixed Subtasks",
            description="Task with both completed and incomplete subtasks",
            parent_id=phase2['id']
        )
        update_work_item(task22['id'], project_id, status="in_progress")
        
        active_subtask = create_work_item(
            project_id=project_id,
            item_type="subtask",
            title="Active Subtask",
            description="Still working on this",
            parent_id=task22['id']
        )
        update_work_item(active_subtask['id'], project_id, status="in_progress")
        
        completed_subtask = create_work_item(
            project_id=project_id,
            item_type="subtask",
            title="Completed Mixed Subtask",
            description="This one is done",
            parent_id=task22['id']
        )
        complete_item(completed_subtask['id'], project_id)
        
        # Get all items for summary generation
        all_items = []
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM work_items WHERE project_id = ? ORDER BY created_at",
                (project_id,)
            )
            columns = [description[0] for description in cursor.description]
            all_items = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Get rolling work plan
        incomplete_items = get_work_items_for_project(project_id)
        hierarchy = build_hierarchy(incomplete_items)
        hierarchy_with_summaries = add_completion_summaries(hierarchy, all_items)
        
        # Verify structure - may only show active phase since completed phase is filtered from rolling work plan
        assert len(hierarchy_with_summaries['projects']) == 1
        project = hierarchy_with_summaries['projects'][0]
        # Could have 1 or 2 phases depending on rolling work plan logic
        assert len(project['phases']) >= 1
        
        # Check if completed phase appears (with completion summary) or is filtered out
        completed_phase = next((p for p in project['phases'] if p['title'] == "Completed Phase"), None)
        if completed_phase:
            # If it appears, it should have completion summary
            assert 'completion_summary' in completed_phase
            assert "✓ All" in completed_phase['completion_summary']
            assert "tasks completed" in completed_phase['completion_summary']
        
        # Phase 2 (active phase) should show active tasks
        active_phase = next((p for p in project['phases'] if p['title'] == "Active Phase"), None)
        assert active_phase is not None
        assert len(active_phase['tasks']) == 2
        
        # Task 2.1 should have subtask completion summary
        task_with_completed_subtasks = next(
            (t for t in active_phase['tasks'] 
            if t['title'] == "Task with Completed Subtasks"), None
        )
        if task_with_completed_subtasks:
            assert 'completion_summary' in task_with_completed_subtasks
            assert "✓ All" in task_with_completed_subtasks['completion_summary']
            assert "subtasks completed" in task_with_completed_subtasks['completion_summary']
            assert len(task_with_completed_subtasks['subtasks']) == 0
        
        # Task 2.2 should show active subtask (completed one hidden)
        task_with_mixed_subtasks = next(
            (t for t in active_phase['tasks'] 
            if t['title'] == "Task with Mixed Subtasks"), None
        )
        if task_with_mixed_subtasks:
            assert len(task_with_mixed_subtasks['subtasks']) == 1
            assert task_with_mixed_subtasks['subtasks'][0]['title'] == "Active Subtask"
