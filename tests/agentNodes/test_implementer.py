from pydantic import TypeAdapter

from src.agentNodes.implementer import Implementer
from src.modelAccessors.base_accessor import BaseModelAccessor
from src.dataModel.model_response import ImplementedResponse
from src.dataModel.task import Task, TaskType


class _StubAccessor(BaseModelAccessor):
    def __init__(self, result: ImplementedResponse) -> None:
        self._result = result

    def call_model(
        self,
        prompt: str,
        *,
        adapter: TypeAdapter[ImplementedResponse],
        schema: dict,
        model: str = "gpt-4",
        system_prompt: str = "",
        tools=None,
    ) -> ImplementedResponse:
        return self._result


def test_implementer_returns_code():
    accessor = _StubAccessor(
        ImplementedResponse(content="def foo(): pass", artifacts=["foo.py"])
    )
    node = Implementer(accessor)
    task = Task(id="i1", description="impl", type=TaskType.IMPLEMENT)
    res = node.execute_task(task)
    assert isinstance(res, ImplementedResponse)
    assert res.artifacts == ["foo.py"]
