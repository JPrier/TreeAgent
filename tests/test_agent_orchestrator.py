import json
from pathlib import Path
from copy import deepcopy

import pytest

import orchestrator
from dataModel.project import Project
from dataModel.task import TaskType, Task
from dataModel.model_response import DecomposedResponse, ImplementedResponse
from modelAccessors.mock_accessor import MockAccessor


class InMemoryStorage:
    """Simple in-memory stand-in for project_manager functions."""

    def __init__(self) -> None:
        self.snapshots: list[tuple[Path, Project]] = []

    def save_project_state(self, project: Project, directory: str | Path) -> Path:
        path = Path(directory) / f"{len(self.snapshots)}.json"
        self.snapshots.append((path, deepcopy(project)))
        return path

    def load_project_state(self, file_path: str | Path) -> Project:
        for p, proj in self.snapshots:
            if p == Path(file_path):
                return deepcopy(proj)
        raise FileNotFoundError(file_path)

    def latest_snapshot_path(self, directory: str | Path) -> Path:
        dir_path = Path(directory)
        candidates = [p for p, _ in self.snapshots if p.parent == dir_path]
        if not candidates:
            raise FileNotFoundError(f"no snapshot in {directory}")
        return sorted(candidates)[-1]

def test_orchestrator_runs_all_tasks(monkeypatch, tmp_path):
    rules = {
        "HLD": {"can_spawn": {"IMPLEMENT": 1}, "self_spawn": False},
        "IMPLEMENT": {"can_spawn": {}, "self_spawn": False},
    }
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(rules))

    def hld_factory(_acc):
        def node(task, config=None):
            assert isinstance(task, Task)
            sub = Task(id="impl", description="impl", type=TaskType.IMPLEMENT)
            return DecomposedResponse(subtasks=[sub]).model_dump()
        return node

    def impl_factory():
        def node(task, config=None):
            assert isinstance(task, Task)
            return ImplementedResponse(content="done").model_dump()
        return node

    node_map = {TaskType.HLD: hld_factory, TaskType.IMPLEMENT: lambda acc: impl_factory()}
    monkeypatch.setattr(orchestrator, "NODE_FACTORY", node_map, raising=False)
    monkeypatch.setattr(orchestrator.orchestrator, "NODE_FACTORY", node_map, raising=False)
    monkeypatch.setattr(
        orchestrator.AgentOrchestrator,
        "_get_accessor",
        lambda self, t: MockAccessor(),
    )

    storage = InMemoryStorage()
    monkeypatch.setattr(orchestrator, "save_project_state", storage.save_project_state)
    monkeypatch.setattr(orchestrator.orchestrator, "save_project_state", storage.save_project_state)

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
        def node(task, config=None):
            assert isinstance(task, Task)
            sub1 = Task(id="impl1", description="impl", type=TaskType.IMPLEMENT)
            sub2 = Task(id="impl2", description="impl", type=TaskType.IMPLEMENT)
            return DecomposedResponse(subtasks=[sub1, sub2]).model_dump()
        return node

    def impl_factory():
        def node(task, config=None):
            assert isinstance(task, Task)
            return ImplementedResponse(content="done").model_dump()
        return node

    node_map = {TaskType.HLD: hld_factory, TaskType.IMPLEMENT: lambda acc: impl_factory()}
    monkeypatch.setattr(orchestrator, "NODE_FACTORY", node_map, raising=False)
    monkeypatch.setattr(
        orchestrator.AgentOrchestrator,
        "_get_accessor",
        lambda self, t: MockAccessor(),
    )

    storage = InMemoryStorage()
    monkeypatch.setattr(orchestrator, "save_project_state", storage.save_project_state)
    monkeypatch.setattr(orchestrator.orchestrator, "save_project_state", storage.save_project_state)

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
        def node(task, config=None):
            assert isinstance(task, Task)
            sub1 = Task(id="impl1", description="i1", type=TaskType.IMPLEMENT)
            sub2 = Task(id="impl2", description="i2", type=TaskType.IMPLEMENT)
            return DecomposedResponse(subtasks=[sub1, sub2]).model_dump()
        return node

    def impl_factory():
        def node(task, config=None):
            assert isinstance(task, Task)
            return ImplementedResponse(content="done").model_dump()
        return node

    node_map = {TaskType.HLD: hld_factory, TaskType.IMPLEMENT: lambda acc: impl_factory()}
    monkeypatch.setattr(orchestrator, "NODE_FACTORY", node_map, raising=False)
    monkeypatch.setattr(
        orchestrator.AgentOrchestrator,
        "_get_accessor",
        lambda self, t: MockAccessor(),
    )

    storage = InMemoryStorage()

    save_calls = {"count": 0}

    def crash_save(project, directory):
        save_calls["count"] += 1
        path = storage.save_project_state(project, directory)
        if save_calls["count"] == 1:
            raise RuntimeError("boom")
        return path

    monkeypatch.setattr(orchestrator.orchestrator, "save_project_state", crash_save)
    monkeypatch.setattr(orchestrator.orchestrator, "load_project_state", storage.load_project_state)
    monkeypatch.setattr(orchestrator.orchestrator, "latest_snapshot_path", storage.latest_snapshot_path)
    monkeypatch.setattr(orchestrator, "save_project_state", crash_save)
    monkeypatch.setattr(orchestrator, "load_project_state", storage.load_project_state)
    monkeypatch.setattr(orchestrator, "latest_snapshot_path", storage.latest_snapshot_path)

    orch = orchestrator.AgentOrchestrator(config_path=str(path))
    with pytest.raises(RuntimeError):
        orch.implement_project("proj", checkpoint_dir=str(checkpoint_base))

    run_dir = storage.snapshots[0][0].parent
    project = orch.resume_project(str(run_dir))

    completed = [t.type for t in project.completedTasks]
    assert completed.count(TaskType.IMPLEMENT) == 2
    assert completed[0] == TaskType.HLD
    assert not project.failedTasks
    assert not project.queuedTasks

def test_self_spawn_blocked(monkeypatch, tmp_path):
    rules = {
        "HLD": {"can_spawn": {"HLD": 2}, "self_spawn": False},
    }
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(rules))

    def hld_factory(_acc):
        def node(task, config=None):
            assert isinstance(task, Task)
            sub1 = Task(id="h1", description="child1", type=TaskType.HLD)
            sub2 = Task(id="h2", description="child2", type=TaskType.HLD)
            return DecomposedResponse(subtasks=[sub1, sub2]).model_dump()
        return node

    monkeypatch.setattr(orchestrator, "NODE_FACTORY", {TaskType.HLD: hld_factory}, raising=False)
    monkeypatch.setattr(
        orchestrator.AgentOrchestrator,
        "_get_accessor",
        lambda self, t: MockAccessor(),
    )

    storage = InMemoryStorage()
    monkeypatch.setattr(orchestrator, "save_project_state", storage.save_project_state)
    monkeypatch.setattr(orchestrator.orchestrator, "save_project_state", storage.save_project_state)

    orch = orchestrator.AgentOrchestrator(config_path=str(path))
    project = orch.implement_project("proj", checkpoint_dir=str(tmp_path))

    assert [t.type for t in project.completedTasks] == [TaskType.HLD]
    assert not project.failedTasks
    assert not project.queuedTasks


def test_checkpoint_written(monkeypatch, tmp_path):
    rules = {
        "HLD": {"can_spawn": {"IMPLEMENT": 1}, "self_spawn": False},
        "IMPLEMENT": {"can_spawn": {}, "self_spawn": False},
    }
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(rules))

    def hld_factory(_acc):
        def node(task, config=None):
            assert isinstance(task, Task)
            sub = Task(id="i", description="impl", type=TaskType.IMPLEMENT)
            return DecomposedResponse(subtasks=[sub]).model_dump()
        return node

    def impl_factory():
        def node(task, config=None):
            assert isinstance(task, Task)
            return ImplementedResponse(content="done").model_dump()
        return node

    node_map = {TaskType.HLD: hld_factory, TaskType.IMPLEMENT: lambda acc: impl_factory()}
    monkeypatch.setattr(orchestrator, "NODE_FACTORY", node_map, raising=False)
    monkeypatch.setattr(
        orchestrator.AgentOrchestrator,
        "_get_accessor",
        lambda self, t: MockAccessor(),
    )

    storage = InMemoryStorage()
    monkeypatch.setattr(orchestrator, "save_project_state", storage.save_project_state)
    monkeypatch.setattr(orchestrator.orchestrator, "save_project_state", storage.save_project_state)
    monkeypatch.setattr(orchestrator, "load_project_state", storage.load_project_state)
    monkeypatch.setattr(orchestrator.orchestrator, "load_project_state", storage.load_project_state)

    orch = orchestrator.AgentOrchestrator(config_path=str(path))
    project = orch.implement_project("proj", checkpoint_dir=str(tmp_path))

    assert storage.snapshots, "no checkpoint files"
    loaded = storage.load_project_state(storage.snapshots[-1][0])
    assert loaded.completedTasks == project.completedTasks

