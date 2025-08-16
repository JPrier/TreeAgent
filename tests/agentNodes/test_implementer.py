from agentNodes.implementer import Implementer
from modelAccessors.base_accessor import BaseModelAccessor
from dataModel.model_response import ImplementedResponse
from dataModel.task import Task, TaskType


class _StubAccessor(BaseModelAccessor):
    def __init__(self, result: ImplementedResponse) -> None:
        self._result = result

    def call_model(self, prompt: str, schema):
        return self._result

    def prompt_model(self, model: str, system_prompt: str, user_prompt: str, schema):  # pragma: no cover - unused
        raise NotImplementedError()

    def execute_task_with_tools(
        self, model: str, system_prompt: str, user_prompt: str, schema, tools=None
    ):  # pragma: no cover - unused
        raise NotImplementedError()


def test_implementer_returns_code():
    accessor = _StubAccessor(
        ImplementedResponse(content="def foo(): pass", artifacts=["foo.py"])
    )
    node = Implementer(accessor)
    task = Task(id="i1", description="impl", type=TaskType.IMPLEMENT)
    res = node.execute_task(task)
    assert isinstance(res, ImplementedResponse)
    assert res.artifacts == ["foo.py"]
