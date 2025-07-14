from agentNodes.hld_designer import HLDDesigner
from dataModel.task import Task, TaskType
from dataModel.model_response import (
    DecomposedResponse,
    ImplementedResponse,
)
from modelAccessors.base_accessor import BaseModelAccessor


class _StubAccessor(BaseModelAccessor):
    def __init__(self, result):
        self._result = result

    def call_model(self, prompt: str, schema):
        return self._result

    def prompt_model(self, model: str, system_prompt: str, user_prompt: str):
        raise NotImplementedError()

    def execute_task_with_tools(self, model: str, system_prompt: str, user_prompt: str, tools=None):
        raise NotImplementedError()


def test_decomposes_when_complex():
    task = Task(id="h1", description="HLD", type=TaskType.HLD, complexity=3)
    subtasks = [
        Task(id=f"h1-{i}", description="sub", type=TaskType.HLD)
        for i in range(task.complexity)
    ]
    accessor = _StubAccessor(DecomposedResponse(subtasks=subtasks))
    node = HLDDesigner(accessor)

    res = node.execute_task(task)

    assert isinstance(res, DecomposedResponse)
    assert len(res.subtasks) == 3
    assert all(st.type == TaskType.HLD for st in res.subtasks)


def test_simple_task_returns_outline():
    task = Task(id="h1", description="HLD", type=TaskType.HLD, complexity=1)
    accessor = _StubAccessor(ImplementedResponse(content="Design"))
    node = HLDDesigner(accessor)

    res = node.execute_task(task)

    assert isinstance(res, ImplementedResponse)
    assert "Design" in (res.content or "")
