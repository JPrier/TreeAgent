from pydantic import TypeAdapter

from agentNodes.implementer import Implementer
from dataModel.model_response import ImplementedResponse
from dataModel.task import Task, TaskType


def test_implementer_returns_code():
    node = Implementer()
    task = Task(id="i1", description="impl", type=TaskType.IMPLEMENT)
    res = node(task, {})
    parsed = TypeAdapter(Implementer.SCHEMA).validate_python(res)
    assert isinstance(parsed, ImplementedResponse)
    assert parsed.artifacts == ["foo.py"]
