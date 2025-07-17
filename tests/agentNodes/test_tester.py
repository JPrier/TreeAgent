from pydantic import TypeAdapter

from agentNodes.tester import Tester
from dataModel.model_response import ImplementedResponse
from dataModel.task import Task, TaskType


def test_tester_passed():
    node = Tester()
    task = Task(id="t1", description="test", type=TaskType.TEST)
    res = node(task, {})
    parsed = TypeAdapter(Tester.SCHEMA).validate_python(res)
    assert isinstance(parsed, ImplementedResponse)
    assert parsed.content == "pytest passed"
