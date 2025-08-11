from src.agentNodes.jury import Jury
from src.dataModel.model_response import ImplementedResponse
from src.dataModel.task import Task, TaskType
from src.modelAccessors.base_accessor import BaseModelAccessor


class _StubAccessor(BaseModelAccessor):
    def prompt_model(self, model: str, system_prompt: str, user_prompt: str):
        raise NotImplementedError()

    def call_model(self, prompt: str, schema):  # pragma: no cover - unused
        raise NotImplementedError()

    def execute_task_with_tools(
        self, model: str, system_prompt: str, user_prompt: str, tools=None
    ):  # pragma: no cover - unused
        raise NotImplementedError()


def test_jury_returns_verdict():
    accessor = _StubAccessor()
    node = Jury(accessor)
    task = Task(id="j1", description="eval", type=TaskType.JURY)
    res = node.execute_task(task)
    assert isinstance(res, ImplementedResponse)
    assert res.content == "jury verdict"

