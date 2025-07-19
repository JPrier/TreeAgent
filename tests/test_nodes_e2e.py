from orchestrator import NODE_FACTORY, AgentOrchestrator, load_project_state
from dataManagement import project_manager
from datetime import datetime, timedelta
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
    "REQUIREMENTS": {"can_spawn": {"HLD": 1}, "self_spawn": False},
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

    def _review_node(task, config=None):
        assert isinstance(task, Task)
        assert task.description == "review"
        return ImplementedResponse(content="reviewed").model_dump()

    def _deploy_node(task, config=None):
        assert isinstance(task, Task)
        assert task.description == "deploy"
        return ImplementedResponse(content="deployed", artifacts=["foo.py"]).model_dump()

    monkeypatch.setitem(NODE_FACTORY, TaskType.REVIEW, lambda acc: _review_node)
    monkeypatch.setitem(NODE_FACTORY, TaskType.TEST, lambda acc: Tester())
    monkeypatch.setitem(NODE_FACTORY, TaskType.DEPLOY, lambda acc: _deploy_node)

    monkeypatch.setattr(AgentOrchestrator, "_get_accessor", lambda self, t: MockAccessor())



    orch = AgentOrchestrator(config_path=str(path))
    project = orch.implement_project("build", checkpoint_dir=str(tmp_path))

    completed = [t.type for t in project.completedTasks]
    assert completed == [
        TaskType.REQUIREMENTS,
        TaskType.HLD,
        TaskType.RESEARCH,
        TaskType.IMPLEMENT,
        TaskType.REVIEW,
        TaskType.TEST,
        TaskType.DEPLOY,
    ]
    assert not project.failedTasks
    assert not project.queuedTasks

    root_task = project.completedTasks[1]
    root_resp = project.taskResults[root_task.id]
    assert isinstance(root_resp, DecomposedResponse)
    assert [t.type for t in root_resp.subtasks] == [
        TaskType.RESEARCH,
        TaskType.IMPLEMENT,
        TaskType.REVIEW,
        TaskType.TEST,
        TaskType.DEPLOY,
    ]
    assert all(t.parent_id == root_task.id for t in root_resp.subtasks)

    research_task, impl_task, review_task, test_task, deploy_task = project.completedTasks[2:]
    assert project.taskResults[research_task.id] == ImplementedResponse(artifacts=["https://example.com"])
    assert project.taskResults[impl_task.id] == ImplementedResponse(content="def foo(): pass", artifacts=["foo.py"])
    assert project.taskResults[review_task.id] == ImplementedResponse(content="reviewed")
    assert project.taskResults[test_task.id] == ImplementedResponse(content="pytest passed")
    assert project.taskResults[deploy_task.id] == ImplementedResponse(content="deployed", artifacts=["foo.py"])

    # ensure each response type occurred at least once
    response_types = {type(resp) for resp in project.taskResults.values()}
    assert DecomposedResponse in response_types
    assert ImplementedResponse in response_types


def test_end_to_end_checkpoint_resume(monkeypatch, tmp_path):
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

    def _review_node(task, config=None):
        assert isinstance(task, Task)
        return ImplementedResponse(content="reviewed").model_dump()

    def _deploy_node(task, config=None):
        assert isinstance(task, Task)
        return ImplementedResponse(content="deployed").model_dump()

    monkeypatch.setitem(NODE_FACTORY, TaskType.REVIEW, lambda acc: _review_node)
    monkeypatch.setitem(NODE_FACTORY, TaskType.TEST, lambda acc: Tester())
    monkeypatch.setitem(NODE_FACTORY, TaskType.DEPLOY, lambda acc: _deploy_node)

    monkeypatch.setattr(AgentOrchestrator, "_get_accessor", lambda self, t: MockAccessor())

    start = datetime(2025, 1, 1)

    class FakeDatetime(datetime):  # type: ignore[misc]
        counter = 0

        @classmethod
        def utcnow(cls):  # type: ignore[override]
            cls.counter += 1
            return start + timedelta(seconds=cls.counter)

    monkeypatch.setattr(project_manager, "datetime", FakeDatetime)

    orch = AgentOrchestrator(config_path=str(path))
    project = orch.implement_project("build", checkpoint_dir=str(tmp_path))

    run_dir = next(p for p in tmp_path.iterdir() if p.is_dir())
    snapshots = sorted(run_dir.glob("*.json"))
    assert snapshots

    expected_total = len(project.completedTasks) + 1
    assert len(snapshots) == expected_total

    for idx, snap in enumerate(snapshots[:-1]):
        loaded = load_project_state(snap)
        completed_ids = [t.id for t in loaded.completedTasks]
        assert completed_ids == [t.id for t in project.completedTasks][: idx + 1]

    loaded = load_project_state(snapshots[-1])
    assert loaded == project

    resumed = orch.resume_project(str(run_dir))
    assert resumed == project
