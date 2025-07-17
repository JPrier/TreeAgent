import json

# ruff: noqa: E402

import importlib
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
dummy_mod = types.ModuleType("modelAccessors.openai_accessor")
dummy_mod.OpenAIAccessor = object  # type: ignore[attr-defined]
sys.modules.setdefault("modelAccessors.openai_accessor", dummy_mod)
dummy_mod2 = types.ModuleType("modelAccessors.anthropic_accessor")
dummy_mod2.AnthropicAccessor = object  # type: ignore[attr-defined]
sys.modules.setdefault("modelAccessors.anthropic_accessor", dummy_mod2)
dummy_mod3 = types.ModuleType("modelAccessors.mock_accessor")
dummy_mod3.MockAccessor = object  # type: ignore[attr-defined]
sys.modules.setdefault("modelAccessors.mock_accessor", dummy_mod3)
orchestrator_mod = importlib.import_module("agent_orchestrator")
from dataModel.task import TaskType
from dataModel.model_response import DecomposedResponse, ImplementedResponse
from dataModel.task import Task


class DummyAccessor:
    def call_model(self, prompt: str, schema):
        raise NotImplementedError

    def prompt_model(self, model: str, system_prompt: str, user_prompt: str):
        raise NotImplementedError

    def execute_task_with_tools(self, model: str, system_prompt: str, user_prompt: str, tools=None):
        raise NotImplementedError


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
        orchestrator_mod,
        "NODE_FACTORY",
        {TaskType.HLD: hld_factory, TaskType.IMPLEMENT: lambda acc: impl_factory()},
        raising=False,
    )
    monkeypatch.setattr(orchestrator_mod.AgentOrchestrator, "_get_accessor", lambda self, t: DummyAccessor())

    orch = orchestrator_mod.AgentOrchestrator(config_path=str(path))
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
        orchestrator_mod,
        "NODE_FACTORY",
        {TaskType.HLD: hld_factory, TaskType.IMPLEMENT: lambda acc: impl_factory()},
        raising=False,
    )
    monkeypatch.setattr(orchestrator_mod.AgentOrchestrator, "_get_accessor", lambda self, t: DummyAccessor())

    orch = orchestrator_mod.AgentOrchestrator(config_path=str(path))
    project = orch.implement_project("proj")

    completed_types = [t.type for t in project.completedTasks]
    assert completed_types.count(TaskType.IMPLEMENT) == 1
    assert not project.failedTasks
    assert not project.queuedTasks
