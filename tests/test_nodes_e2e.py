import pathlib
import sys
import types

# ruff: noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
dummy_mod = types.ModuleType("modelAccessors.openai_accessor")
dummy_mod.OpenAIAccessor = object
sys.modules.setdefault("modelAccessors.openai_accessor", dummy_mod)
dummy_mod2 = types.ModuleType("modelAccessors.anthropic_accessor")
dummy_mod2.AnthropicAccessor = object
sys.modules.setdefault("modelAccessors.anthropic_accessor", dummy_mod2)
dummy_mod3 = types.ModuleType("modelAccessors.mock_accessor")
dummy_mod3.MockAccessor = object
sys.modules.setdefault("modelAccessors.mock_accessor", dummy_mod3)
from agent_orchestrator import NODE_FACTORY, AgentOrchestrator
from agentNodes.researcher import Researcher
from agentNodes.hld_designer import HLDDesigner
from agentNodes.implementer import Implementer
from agentNodes.tester import Tester
from modelAccessors.base_accessor import BaseModelAccessor
from dataModel.task import Task, TaskType
from dataModel.model_response import (
    DecomposedResponse,
    ImplementedResponse,
)
import json



class _StubAccessor(BaseModelAccessor):
    def __init__(self, call_model_callback=None, exec_with_tools_callback=None):
        self._call_model_callback = call_model_callback
        self._exec_with_tools_callback = exec_with_tools_callback

    def call_model(self, prompt: str, schema):
        if not self._call_model_callback:
            raise NotImplementedError()
        return self._call_model_callback(prompt, schema)

    def prompt_model(self, model: str, system_prompt: str, user_prompt: str):
        raise NotImplementedError()

    def execute_task_with_tools(self, model: str, system_prompt: str, user_prompt: str, tools=None):
        if not self._exec_with_tools_callback:
            raise NotImplementedError()
        return self._exec_with_tools_callback(model, system_prompt, user_prompt, tools)


def _hld_call_model(prompt: str, schema):
    subtasks = [
        Task(id="r1", description="research", type=TaskType.RESEARCH),
        Task(id="i1", description="impl", type=TaskType.IMPLEMENT),
        Task(id="v1", description="review", type=TaskType.REVIEW),
        Task(id="t1", description="test", type=TaskType.TEST),
        Task(id="d1", description="deploy", type=TaskType.DEPLOY),
    ]
    return DecomposedResponse(subtasks=subtasks)


def _research_exec(model: str, system_prompt: str, user_prompt: str, tools=None):
    return ImplementedResponse(artifacts=["https://example.com"])


RULES = {
    "HLD": {"can_spawn": {"RESEARCH": 1, "IMPLEMENT": 1, "REVIEW": 1, "TEST": 1, "DEPLOY": 1}, "self_spawn": False},
    "RESEARCH": {"can_spawn": {}, "self_spawn": False},
    "IMPLEMENT": {"can_spawn": {}, "self_spawn": False},
    "REVIEW": {"can_spawn": {}, "self_spawn": False},
    "TEST": {"can_spawn": {}, "self_spawn": False},
    "DEPLOY": {"can_spawn": {}, "self_spawn": False},
}


def test_end_to_end_chain(monkeypatch, tmp_path):
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(RULES))

    monkeypatch.setitem(
        NODE_FACTORY,
        TaskType.HLD,
        lambda acc: HLDDesigner(_StubAccessor(_hld_call_model)),
    )
    monkeypatch.setitem(
        NODE_FACTORY,
        TaskType.RESEARCH,
        lambda acc: Researcher(_StubAccessor(exec_with_tools_callback=_research_exec)),
    )
    monkeypatch.setitem(NODE_FACTORY, TaskType.IMPLEMENT, lambda acc: Implementer())

    def _review_node(state, config=None):
        return ImplementedResponse(content="reviewed").model_dump()

    def _deploy_node(state, config=None):
        return ImplementedResponse(content="deployed", artifacts=["foo.py"]).model_dump()

    monkeypatch.setitem(NODE_FACTORY, TaskType.REVIEW, lambda acc: _review_node)
    monkeypatch.setitem(NODE_FACTORY, TaskType.TEST, lambda acc: Tester())
    monkeypatch.setitem(NODE_FACTORY, TaskType.DEPLOY, lambda acc: _deploy_node)

    monkeypatch.setattr(AgentOrchestrator, "_get_accessor", lambda self, t: _StubAccessor())

    orch = AgentOrchestrator(config_path=str(path))
    project = orch.implement_project("build")

    completed = [t.type for t in project.completedTasks]
    assert completed == [
        TaskType.HLD,
        TaskType.RESEARCH,
        TaskType.IMPLEMENT,
        TaskType.REVIEW,
        TaskType.TEST,
        TaskType.DEPLOY,
    ]
    assert not project.failedTasks
    assert not project.queuedTasks
