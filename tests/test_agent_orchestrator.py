import json

import orchestrator
from dataModel.task import TaskType, Task
from dataModel.model_response import DecomposedResponse, ImplementedResponse
from modelAccessors.mock_accessor import MockAccessor

def test_orchestrator_runs_all_tasks(monkeypatch, tmp_path):
    rules = {
        "HLD": {"can_spawn": {"IMPLEMENT": 1}, "self_spawn": False},
        "IMPLEMENT": {"can_spawn": {}, "self_spawn": False},
    }
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(rules))

    def hld_factory(_acc):
        def node(state, config=None):
            sub = Task(id="impl", description="impl", type=TaskType.IMPLEMENT)
            return DecomposedResponse(subtasks=[sub]).model_dump()
        return node

    def impl_factory():
        def node(state, config=None):
            return ImplementedResponse(content="done").model_dump()
        return node

    monkeypatch.setattr(
        orchestrator,
        "NODE_FACTORY",
        {TaskType.HLD: hld_factory, TaskType.IMPLEMENT: lambda acc: impl_factory()},
        raising=False,
    )
    monkeypatch.setattr(
        orchestrator.AgentOrchestrator,
        "_get_accessor",
        lambda self, t: MockAccessor(),
    )

    orch = orchestrator.AgentOrchestrator(config_path=str(path))
    project = orch.implement_project("proj")

    assert [t.type for t in project.completedTasks] == [TaskType.HLD, TaskType.IMPLEMENT]
    assert not project.failedTasks
    assert not project.inProgressTasks
    assert not project.queuedTasks


def test_spawn_rule_limit(monkeypatch, tmp_path):
    rules = {
        "HLD": {"can_spawn": {"IMPLEMENT": 1}, "self_spawn": False},
        "IMPLEMENT": {"can_spawn": {}, "self_spawn": False},
    }
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(rules))

    def hld_factory(_acc):
        def node(state, config=None):
            sub1 = Task(id="impl1", description="impl", type=TaskType.IMPLEMENT)
            sub2 = Task(id="impl2", description="impl", type=TaskType.IMPLEMENT)
            return DecomposedResponse(subtasks=[sub1, sub2]).model_dump()
        return node

    def impl_factory():
        def node(state, config=None):
            return ImplementedResponse(content="done").model_dump()
        return node

    monkeypatch.setattr(
        orchestrator,
        "NODE_FACTORY",
        {TaskType.HLD: hld_factory, TaskType.IMPLEMENT: lambda acc: impl_factory()},
        raising=False,
    )
    monkeypatch.setattr(
        orchestrator.AgentOrchestrator,
        "_get_accessor",
        lambda self, t: MockAccessor(),
    )

    orch = orchestrator.AgentOrchestrator(config_path=str(path))
    project = orch.implement_project("proj")

    completed_types = [t.type for t in project.completedTasks]
    assert completed_types.count(TaskType.IMPLEMENT) == 1
    assert not project.failedTasks
    assert not project.queuedTasks
