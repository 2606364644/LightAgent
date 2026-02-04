"""
Tests for workflow module

Run with: pytest tests/test_workflow.py -v

Installation:
    pip install lightagent-workflow
"""
import pytest
import asyncio
from pathlib import Path
import tempfile
import os

from lightagent_workflow import (
    PromptTemplate,
    PromptManager,
    MultiPartPrompt,
    TaskGraph,
    Task,
    TaskPriority,
    create_workflow_engine
)
from lightagent_workflow.planning import (
    SimplePlanner,
    TaskExecutor,
    LLMPlanner
)
from lightagent import (
    create_file_tools,
    FileToolConfig,
    SafePathConfig
)


class TestPromptTemplates:
    """Test prompt template functionality"""

    def test_basic_template(self):
        """Test basic template formatting"""
        template = PromptTemplate(
            template="Hello {{name}}, you are a {{role}}.",
            description="Test template"
        )

        result = template.format(name="Alice", role="developer")
        assert result == "Hello Alice, you are a developer."

    def test_variable_validation(self):
        """Test variable validation"""
        template = PromptTemplate(
            template="Task: {{task}}, Priority: {{priority}}",
            description="Validation test"
        )

        # Should pass with all required variables
        assert template.validate(task="test", priority="high")

        # Should fail without required variables
        assert not template.validate(task="test")

    def test_optional_variables(self):
        """Test optional variables with defaults"""
        template = PromptTemplate(
            template="Name: {{name}}, Age: {{age:30}}",
            description="Optional variables test"
        )

        result = template.format(name="Bob")
        assert result == "Name: Bob, Age: 30"

    def test_template_composition(self):
        """Test composing multiple templates"""
        t1 = PromptTemplate(template="Part 1: {{a}}")
        t2 = PromptTemplate(template="Part 2: {{b}}")

        composed = t1.compose(t2)
        result = composed.format(a="first", b="second")

        assert "Part 1: first" in result
        assert "Part 2: second" in result

    def test_multipart_prompt(self):
        """Test multipart prompts"""
        system = PromptTemplate(template="You are a {{role}}")
        user = PromptTemplate(template="Task: {{task}}")

        multipart = MultiPartPrompt(system=system, user=user)
        messages = multipart.to_messages(role="expert", task="test")

        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[1]['role'] == 'user'


class TestPromptManager:
    """Test prompt manager functionality"""

    def test_register_and_retrieve(self):
        """Test registering and retrieving templates"""
        manager = PromptManager()
        template = PromptTemplate(template="Test: {{value}}")

        manager.register_template('test.template', template, category='test')

        retrieved = manager.get_template('test.template')
        assert retrieved is not None
        assert retrieved.template == "Test: {{value}}"

    def test_list_templates(self):
        """Test listing templates"""
        manager = PromptManager()

        manager.create_template_from_string(
            'template1',
            'Template 1: {{a}}',
            category='cat1'
        )
        manager.create_template_from_string(
            'template2',
            'Template 2: {{b}}',
            category='cat1'
        )

        # List all
        all_templates = manager.list_templates()
        assert len(all_templates) >= 2

        # List by category
        cat1_templates = manager.list_templates(category='cat1')
        assert len(cat1_templates) == 2

    def test_compose_templates(self):
        """Test composing templates via manager"""
        manager = PromptManager()

        manager.create_template_from_string('t1', 'First: {{a}}')
        manager.create_template_from_string('t2', 'Second: {{b}}')

        composed = manager.compose_templates('combined', ['t1', 't2'])

        result = composed.format(a="1", b="2")
        assert "First: 1" in result
        assert "Second: 2" in result


class TestTaskGraph:
    """Test task graph functionality"""

    def test_task_creation(self):
        """Test creating tasks"""
        task = Task(
            name="Test Task",
            description="A test task",
            priority=TaskPriority.HIGH
        )

        assert task.name == "Test Task"
        assert task.status == "pending"
        assert task.priority == "high"

    def test_task_dependencies(self):
        """Test task dependencies"""
        graph = TaskGraph()

        task1 = Task(name="Task 1", description="First task")
        task2 = Task(name="Task 2", description="Second task")

        graph.add_task(task1)
        graph.add_task(task2)
        graph.add_dependency(task2.task_id, task1.task_id)

        # Task 2 should depend on task 1
        assert task1.task_id in task2.dependencies
        assert task2.task_id in task1.dependents

    def test_ready_tasks(self):
        """Test getting ready tasks"""
        graph = TaskGraph()

        task1 = Task(name="Task 1", description="First")
        task2 = Task(name="Task 2", description="Second")
        task3 = Task(name="Task 3", description="Third")

        graph.add_task(task1)
        graph.add_task(task2)
        graph.add_task(task3)

        graph.add_dependency(task2.task_id, task1.task_id)
        graph.add_dependency(task3.task_id, task1.task_id)

        # Only task1 should be ready
        ready = graph.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].task_id == task1.task_id

    def test_execution_order(self):
        """Test execution order calculation"""
        graph = TaskGraph()

        task1 = Task(name="1", description="First")
        task2 = Task(name="2", description="Second")
        task3 = Task(name="3", description="Third")

        graph.add_task(task1)
        graph.add_task(task2)
        graph.add_task(task3)

        graph.add_dependency(task2.task_id, task1.task_id)
        graph.add_dependency(task3.task_id, task2.task_id)

        levels = graph.get_execution_order()

        # Should have 3 levels
        assert len(levels) == 3
        assert len(levels[0]) == 1  # First level has task1
        assert len(levels[1]) == 1  # Second level has task2
        assert len(levels[2]) == 1  # Third level has task3

    def test_circular_dependency_detection(self):
        """Test circular dependency detection"""
        graph = TaskGraph()

        task1 = Task(name="1", description="First")
        task2 = Task(name="2", description="Second")

        graph.add_task(task1)
        graph.add_task(task2)

        # Create circular dependency
        graph.add_dependency(task1.task_id, task2.task_id)
        graph.add_dependency(task2.task_id, task1.task_id)

        errors = graph.validate_dependencies()
        assert len(errors) > 0
        assert "circular" in errors[0].lower()

    def test_task_status_changes(self):
        """Test task status transitions"""
        task = Task(name="Test", description="Test task")

        assert task.status == "pending"

        task.mark_started()
        assert task.status == "in_progress"
        assert task.started_at is not None

        task.mark_completed(result="done")
        assert task.status == "completed"
        assert task.completed_at is not None
        assert task.result == "done"


class TestFileTools:
    """Test file system tools"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def safe_config(self, temp_dir):
        """Create safe file tool config"""
        return FileToolConfig(
            safe_mode=True,
            path_config=SafePathConfig(
                allowed_roots=[temp_dir],
                max_file_size=1024
            )
        )

    def test_write_and_read_file(self, temp_dir, safe_config):
        """Test writing and reading files"""
        import asyncio

        async def test():
            from lightagent.tools import write_file, read_file

            # Write file
            test_path = os.path.join(temp_dir, "test.txt")
            write_result = await write_file(
                test_path,
                "Hello, World!",
                config=safe_config
            )
            assert write_result['success']

            # Read file
            read_result = await read_file(test_path, config=safe_config)
            assert read_result['success']
            assert read_result['content'] == "Hello, World!"

        asyncio.run(test())

    def test_path_validation(self, temp_dir):
        """Test path validation"""
        config = SafePathConfig(
            allowed_roots=[temp_dir]
        )

        from lightagent.tools import validate_path_safe

        # Allowed path
        is_safe, _ = validate_path_safe(temp_dir, config)
        assert is_safe

        # Not allowed path
        is_safe, error = validate_path_safe("/etc/passwd", config)
        assert not is_safe
        assert error is not None

    def test_list_directory(self, temp_dir, safe_config):
        """Test listing directory"""
        import asyncio

        async def test():
            from lightagent.tools import list_directory

            # Create some test files
            for i in range(3):
                path = os.path.join(temp_dir, f"file{i}.txt")
                with open(path, 'w') as f:
                    f.write(f"content {i}")

            # List directory
            result = await list_directory(temp_dir, config=safe_config)
            assert result['success']
            assert result['count'] == 3

        asyncio.run(test())


class TestPlanning:
    """Test planning functionality"""

    @pytest.mark.asyncio
    async def test_simple_planner(self):
        """Test simple planner"""
        planner = SimplePlanner()

        plan = await planner.plan("Test goal")

        assert len(plan) >= 1
        assert plan[0]['description'] == "Test goal"

    @pytest.mark.asyncio
    async def test_plan_refinement(self):
        """Test plan refinement"""
        planner = SimplePlanner()

        original_plan = await planner.plan("Original goal")
        refined_plan = await planner.refine_plan(original_plan, "Make it better")

        # Simple planner doesn't refine, so should be same
        assert len(refined_plan) == len(original_plan)


class TestWorkflowEngine:
    """Test workflow engine"""

    @pytest.mark.asyncio
    async def test_engine_initialization(self):
        """Test engine initialization"""
        engine = await create_workflow_engine(agent=None, verbose=False)

        assert engine is not None
        assert len(engine.get_available_prompts()) > 0

    @pytest.mark.asyncio
    async def test_direct_execution(self):
        """Test direct execution without planning"""
        engine = await create_workflow_engine(agent=None, verbose=False)
        engine.enable_planning = False

        # This should work even without agent for simple cases
        # but will fail for complex operations
        result = await engine.execute("Test goal")

        assert 'success' in result


class TestIntegration:
    """Integration tests"""

    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test complete workflow with planning and execution"""
        from lightagent.workflow.planning import SimplePlanner, TaskExecutor

        # Create planner and executor
        planner = SimplePlanner()
        executor = TaskExecutor(agent=None)

        # Plan a goal
        plan = await planner.plan("Test workflow")

        # Create task graph
        graph = TaskGraph()
        for i, task_def in enumerate(plan):
            task = Task(
                name=task_def.get('name', f'Task {i}'),
                description=task_def.get('description', ''),
                priority=task_def.get('priority', 'medium')
            )
            graph.add_task(task)

        # Execute
        summary = await executor.execute_plan(graph, mode='sequential')

        assert 'total' in summary
        assert summary['total'] == len(plan)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
