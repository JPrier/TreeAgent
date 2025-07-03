from pydantic import TypeAdapter
from agentNodes.hld_designer import HLDDesigner
from dataModel.task import Task, TaskType
from dataModel.model_response import DecomposedResponse, ImplementedResponse


def test_hld_designer_decomposes():
    node = HLDDesigner()
    task = Task(id="h1", description="HLD", type=TaskType.HLD, complexity=3)
    state = {"task_queue": [task]}
    res = node(state, {})
    parsed = TypeAdapter(HLDDesigner.SCHEMA).validate_python(res)
    assert isinstance(parsed, DecomposedResponse)
    assert len(parsed.subtasks) == 3
    assert all(st.type == TaskType.HLD for st in parsed.subtasks)


def test_hld_designer_implemented():
    node = HLDDesigner()
    task = Task(id="h1", description="HLD", type=TaskType.HLD, complexity=1)
    state = {"task_queue": [task]}
    res = node(state, {})
    parsed = TypeAdapter(HLDDesigner.SCHEMA).validate_python(res)
    assert isinstance(parsed, ImplementedResponse)
