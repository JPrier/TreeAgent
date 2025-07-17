from orchestrator import NODE_FACTORY, AgentOrchestrator
from agentNodes.researcher import Researcher
from agentNodes.hld_designer import HLDDesigner
from agentNodes.implementer import Implementer
from agentNodes.tester import Tester
from modelAccessors.mock_accessor import MockAccessor
from dataModel.task import Task, TaskType
from dataModel.model_response import (
    DecomposedResponse,
    ImplementedResponse,
)
import json


def _patch_accessor(accessor: MockAccessor, *, call_model=None, exec_tools=None) -> MockAccessor:
    if call_model:
        def patched_prompt(model: str, system_prompt: str, user_prompt: str):
            return call_model(user_prompt, None)
        accessor.prompt_model = patched_prompt  # type: ignore
    if exec_tools:
        def patched_exec(model: str, system_prompt: str, user_prompt: str, tools=None):
            return exec_tools(model, system_prompt, user_prompt, tools)
        accessor.execute_task_with_tools = patched_exec  # type: ignore
    return accessor


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
        lambda acc: HLDDesigner(_patch_accessor(acc, call_model=_hld_call_model)),
    )
    monkeypatch.setitem(
        NODE_FACTORY,
        TaskType.RESEARCH,
        lambda acc: Researcher(_patch_accessor(acc, exec_tools=_research_exec)),
    )
    monkeypatch.setitem(NODE_FACTORY, TaskType.IMPLEMENT, lambda acc: Implementer())

    def _review_node(state, config=None):
        return ImplementedResponse(content="reviewed").model_dump()

    def _deploy_node(state, config=None):
        return ImplementedResponse(content="deployed", artifacts=["foo.py"]).model_dump()

    monkeypatch.setitem(NODE_FACTORY, TaskType.REVIEW, lambda acc: _review_node)
    monkeypatch.setitem(NODE_FACTORY, TaskType.TEST, lambda acc: Tester())
    monkeypatch.setitem(NODE_FACTORY, TaskType.DEPLOY, lambda acc: _deploy_node)

    monkeypatch.setattr(AgentOrchestrator, "_get_accessor", lambda self, t: MockAccessor())

    orch = AgentOrchestrator(config_path=str(path))
    project = orch.implement_project("build", checkpoint_dir=str(tmp_path))

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
