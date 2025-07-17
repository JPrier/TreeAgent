import json
import pytest

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
        orchestrator.orchestrator,
        "NODE_FACTORY",
        {TaskType.HLD: hld_factory, TaskType.IMPLEMENT: lambda acc: impl_factory()},
        raising=False,
    )
    monkeypatch.setattr(
        orchestrator.orchestrator,
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
    project = orch.implement_project("proj", checkpoint_dir=str(tmp_path))

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
    project = orch.implement_project("proj", checkpoint_dir=str(tmp_path))

    completed_types = [t.type for t in project.completedTasks]
    assert completed_types.count(TaskType.IMPLEMENT) == 1
    assert not project.failedTasks
    assert not project.queuedTasks


def test_resume_from_checkpoint(monkeypatch, tmp_path):
    rules = {
        "HLD": {"can_spawn": {"IMPLEMENT": 2}, "self_spawn": False},
        "IMPLEMENT": {"can_spawn": {}, "self_spawn": False},
    }
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(rules))
    checkpoint_base = tmp_path

    def hld_factory(_acc):
        def node(state, config=None):
            sub1 = Task(id="impl1", description="i1", type=TaskType.IMPLEMENT)
            sub2 = Task(id="impl2", description="i2", type=TaskType.IMPLEMENT)
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

    save_calls = {"count": 0}
    orig_save = orchestrator.save_project_state

    def crash_save(project, path):
        save_calls["count"] += 1
        orig_save(project, path)
        if save_calls["count"] == 1:
            raise RuntimeError("boom")

    monkeypatch.setattr(orchestrator.orchestrator, "save_project_state", crash_save)

    orch = orchestrator.AgentOrchestrator(config_path=str(path))
    with pytest.raises(RuntimeError):
        orch.implement_project("proj", checkpoint_dir=str(checkpoint_base))

    monkeypatch.setattr(orchestrator.orchestrator, "save_project_state", orig_save)
    run_dir = next(p for p in checkpoint_base.iterdir() if p.is_dir())
    project = orch.resume_project(str(run_dir))

    completed = [t.type for t in project.completedTasks]
    assert completed.count(TaskType.IMPLEMENT) == 2
    assert completed[0] == TaskType.HLD
    assert not project.failedTasks
    assert not project.queuedTasks
