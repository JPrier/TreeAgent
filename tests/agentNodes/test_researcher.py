import pytest
from pydantic import TypeAdapter, ValidationError

from agentNodes.researcher import Researcher
from tools.web_search import WEB_SEARCH_TOOL
from dataModel.model_response import ImplementedResponse
from dataModel.task import Task, TaskType
from modelAccessors.base_accessor import BaseModelAccessor


class _StubAccessor(BaseModelAccessor):
    def __init__(self, result):
        self._result = result

    def prompt_model(self, model: str, system_prompt: str, user_prompt: str):
        raise NotImplementedError()

    def execute_task_with_tools(self, model: str, system_prompt: str, user_prompt: str, tools=None):
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
        TypeAdapter(Researcher.SCHEMA).validate_python(node.execute_task(task))

