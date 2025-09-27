import pytest
from pydantic import TypeAdapter, ValidationError

from src.agentNodes.researcher import Researcher
from src.tools.web_search import WEB_SEARCH_TOOL
from src.dataModel.model_response import ImplementedResponse
from src.dataModel.task import Task, TaskType
from src.modelAccessors.base_accessor import BaseModelAccessor


class _StubAccessor(BaseModelAccessor):
    def __init__(self, result):
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


def test_researcher_returns_urls():
    accessor = _StubAccessor(
        ImplementedResponse(artifacts=["https://foo.com", "https://bar.com"])
    )
    node = Researcher(accessor)

    task = Task(id="r1", description="search", type=TaskType.RESEARCH)
    res = node.execute_task(task)

    assert isinstance(res, ImplementedResponse)
    assert res.artifacts == ["https://foo.com", "https://bar.com"]
    assert task.tools == [WEB_SEARCH_TOOL]


def test_researcher_schema_validation():
    class _Bad:
        def model_dump(self):
            return {"not": "valid"}

    accessor = _StubAccessor(_Bad())
    node = Researcher(accessor)
    task = Task(id="r1", description="search", type=TaskType.RESEARCH)

    with pytest.raises(ValidationError):
        Researcher.ADAPTER.validate_python(node.execute_task(task))

