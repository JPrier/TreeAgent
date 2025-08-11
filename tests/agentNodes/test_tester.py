from src.agentNodes.tester import Tester
from src.modelAccessors.base_accessor import BaseModelAccessor
from src.dataModel.model_response import ImplementedResponse
from src.dataModel.task import Task, TaskType


class _StubAccessor(BaseModelAccessor):
    def __init__(self, result: ImplementedResponse) -> None:
        self._result = result

    def call_model(self, prompt: str, schema):
        return self._result

    def prompt_model(self, model: str, system_prompt: str, user_prompt: str):  # pragma: no cover - unused
        raise NotImplementedError()

    def execute_task_with_tools(self, model: str, system_prompt: str, user_prompt: str, tools=None):  # pragma: no cover - unused
        raise NotImplementedError()


def test_tester_passed():
    accessor = _StubAccessor(ImplementedResponse(content="pytest passed"))
    node = Tester(accessor)
    task = Task(id="t1", description="test", type=TaskType.TEST)
    res = node.execute_task(task)
    assert isinstance(res, ImplementedResponse)
    assert res.content == "pytest passed"
