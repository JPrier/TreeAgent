from types import SimpleNamespace

from agent_nodes.hld_designer import HLDDesigner
from dataModel.task import Task, TaskType
from dataModel.model_response import DecomposedResponse, ImplementedResponse


def test_decomposes_when_complex():
    task = Task(id="t1", description="design", type=TaskType.HLD, complexity=3)
    subtasks = [
        Task(id=f"t1-{i}", description="sub", type=TaskType.HLD)
        for i in range(task.complexity)
    ]
    accessor = SimpleNamespace(call_model=lambda prompt, schema: DecomposedResponse(subtasks=subtasks))
    node = HLDDesigner(accessor)

    res = node.execute_task(task)

    assert isinstance(res, DecomposedResponse)
    assert len(res.subtasks) == task.complexity


def test_simple_task_returns_outline():
    task = Task(id="t1", description="design", type=TaskType.HLD, complexity=1)
    accessor = SimpleNamespace(call_model=lambda prompt, schema: ImplementedResponse(content="Design outline"))
    node = HLDDesigner(accessor)

    res = node.execute_task(task)

    assert isinstance(res, ImplementedResponse)
    assert "Design" in (res.content or "")
