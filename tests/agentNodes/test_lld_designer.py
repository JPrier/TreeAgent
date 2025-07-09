import pytest
from pydantic import TypeAdapter, ValidationError

from agentNodes.lld_designer import LLDDesigner
from dataModel.model_response import ImplementedResponse
from dataModel.task import Task, TaskType
from modelAccessors.base_accessor import BaseModelAccessor


class _StubAccessor(BaseModelAccessor):
    def __init__(self, result: ImplementedResponse | None = None):
        self._result = result or ImplementedResponse(content="x" * 25)

    def call_model(self, prompt: str, schema):
        return self._result

    def prompt_model(self, model: str, system_prompt: str, user_prompt: str):
        raise NotImplementedError()

    def execute_task_with_tools(self, model: str, system_prompt: str, user_prompt: str, tools=None):
        raise NotImplementedError()


def test_lld_returns_content():
    accessor = _StubAccessor(ImplementedResponse(content="a" * 30))
    node = LLDDesigner(accessor)
    task = Task(id="l1", description="Design component", type=TaskType.LLD)
    res = node.execute_task(task)

    assert isinstance(res, ImplementedResponse)
    assert len(res.content or "") > 20


def test_schema_enforced(monkeypatch):
    accessor = _StubAccessor()
    node = LLDDesigner(accessor)
    monkeypatch.setattr(node.llm_accessor, "call_model", lambda prompt, schema: object())
    task = Task(id="l2", description="Bad", type=TaskType.LLD)

    with pytest.raises(ValidationError):
        TypeAdapter(LLDDesigner.SCHEMA).validate_python(node.execute_task(task))
