from types import SimpleNamespace

from agentNodes.hld_designer import HLDDesigner
from dataModel.task import Task, TaskType
from dataModel.model_response import DecomposedResponse, ImplementedResponse


def test_hld_designer_decomposes():
    task = Task(id="h1", description="HLD", type=TaskType.HLD, complexity=3)
    subtasks = [
        Task(id=f"h1-{i}", description="sub", type=TaskType.HLD)
        for i in range(task.complexity)
    ]
    accessor = SimpleNamespace(call_model=lambda prompt, schema: DecomposedResponse(subtasks=subtasks))
    node = HLDDesigner(accessor)

    res = node.execute_task(task)

    assert isinstance(res, DecomposedResponse)
    assert len(res.subtasks) == 3
    assert all(st.type == TaskType.HLD for st in res.subtasks)


def test_hld_designer_implemented():
    task = Task(id="h1", description="HLD", type=TaskType.HLD, complexity=1)
    accessor = SimpleNamespace(call_model=lambda prompt, schema: ImplementedResponse(content="Design"))
    node = HLDDesigner(accessor)

    res = node.execute_task(task)

    assert isinstance(res, ImplementedResponse)
