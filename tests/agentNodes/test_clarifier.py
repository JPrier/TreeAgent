from agentNodes.clarifier import Clarifier
from dataModel.task import Task, TaskType
from dataModel.model_response import FollowUpResponse, ImplementedResponse
from modelAccessors.base_accessor import BaseModelAccessor


class _StubAccessor(BaseModelAccessor):
    def __init__(self, result):
        self._result = result

    def call_model(self, prompt: str, schema):
        return self._result

    def prompt_model(self, model: str, system_prompt: str, user_prompt: str):
        raise NotImplementedError()

    def execute_task_with_tools(self, model: str, system_prompt: str, user_prompt: str, tools=None):
        raise NotImplementedError()


def test_needs_followup():
    follow_task = Task(id="f1", description="Need more details", type=TaskType.REQUIREMENTS)
    response = FollowUpResponse(follow_up_ask=follow_task)
    node = Clarifier(_StubAccessor(response))

    result = node.execute_task(Task(id="t1", description="Build?", type=TaskType.REQUIREMENTS))
    assert isinstance(result, FollowUpResponse)
    assert isinstance(result.follow_up_ask, Task)


def test_no_followup():
    response = ImplementedResponse(content="Requirements are clear")
    node = Clarifier(_StubAccessor(response))

    result = node.execute_task(Task(id="t2", description="Build", type=TaskType.REQUIREMENTS))
    assert isinstance(result, ImplementedResponse)
    assert result.content == "Requirements are clear"
