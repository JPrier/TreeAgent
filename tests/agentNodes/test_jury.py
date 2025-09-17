from pydantic import TypeAdapter

from src.agentNodes.jury import Jury
from src.dataModel.model_response import ImplementedResponse, ModelResponse
from src.dataModel.task import Task, TaskType
from src.modelAccessors.base_accessor import BaseModelAccessor


class _StubAccessor(BaseModelAccessor):
    def call_model(
        self,
        prompt: str,
        *,
        adapter: TypeAdapter[ModelResponse],
        schema: dict,
        model: str = "gpt-4",
        system_prompt: str = "",
        tools=None,
    ) -> ModelResponse:  # pragma: no cover - unused
        raise NotImplementedError()


def test_jury_returns_verdict():
    accessor = _StubAccessor()
    node = Jury(accessor)
    task = Task(id="j1", description="eval", type=TaskType.JURY)
    res = node.execute_task(task)
    assert isinstance(res, ImplementedResponse)
    assert res.content == "jury verdict"

