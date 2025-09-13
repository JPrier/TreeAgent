from pydantic import TypeAdapter

from src.agentNodes.tester import Tester
from src.modelAccessors.base_accessor import BaseModelAccessor
from src.dataModel.model_response import (
    ImplementedResponse,
    ModelResponse,
)
from src.dataModel.task import Task, TaskType


class _StubAccessor(BaseModelAccessor):
    def __init__(self, result: ImplementedResponse) -> None:
        self._result = result

    def call_model(
        self,
        prompt: str,
        *,
        adapter: TypeAdapter[ModelResponse],
        schema: dict,
        model: str = "gpt-4",
        system_prompt: str = "",
        tools=None,
    ) -> ModelResponse:
        return self._result


def test_tester_passed():
    accessor = _StubAccessor(ImplementedResponse(content="pytest passed"))
    node = Tester(accessor)
    task = Task(id="t1", description="test", type=TaskType.TEST)
    res = node.execute_task(task)
    assert isinstance(res, ImplementedResponse)
    assert res.content == "pytest passed"
