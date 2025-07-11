from agentNodes.clarifier import Clarifier
from modelAccessors.base_accessor import BaseModelAccessor
from dataModel.task import Task, TaskType
from dataModel.model_response import FollowUpResponse, ImplementedResponse


class _StubAccessor(BaseModelAccessor):
    def call_model(self, prompt: str, schema):
        raise NotImplementedError()

    def prompt_model(self, model: str, system_prompt: str, user_prompt: str):
        raise NotImplementedError()

    def execute_task_with_tools(self, model: str, system_prompt: str, user_prompt: str, tools=None):
        raise NotImplementedError()


def test_needs_followup(monkeypatch):
    follow_up = Task(id="t1-fu", description="Need more details", type=TaskType.REQUIREMENTS)
    accessor = _StubAccessor()
    node = Clarifier(accessor)
    monkeypatch.setattr(node.llm_accessor, "call_model", lambda prompt, schema: FollowUpResponse(follow_up_ask=follow_up))
    task = Task(id="t1", description="Build app?", type=TaskType.REQUIREMENTS)

    res = node.execute_task(task)

    assert isinstance(res, FollowUpResponse)
    assert res.follow_up_ask == follow_up


def test_no_followup(monkeypatch):
    accessor = _StubAccessor()
    node = Clarifier(accessor)
    monkeypatch.setattr(node.llm_accessor, "call_model", lambda prompt, schema: ImplementedResponse(content="Requirements are clear"))
    task = Task(id="t2", description="All good", type=TaskType.REQUIREMENTS)

    res = node.execute_task(task)

    assert isinstance(res, ImplementedResponse)
    assert res.content == "Requirements are clear"
