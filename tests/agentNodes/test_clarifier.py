from pydantic import TypeAdapter
from agentNodes.clarifier import Clarifier
from dataModel.task import Task, TaskType
from dataModel.model_response import FollowUpResponse, ImplementedResponse


def test_clarifier_followup():
    node = Clarifier()
    state = {"root_task": Task(id="t1", description="Need specs?", type=TaskType.REQUIREMENTS)}
    res = node(state, {})
    parsed = TypeAdapter(Clarifier.SCHEMA).validate_python(res)
    assert isinstance(parsed, FollowUpResponse)


def test_clarifier_implemented():
    node = Clarifier()
    state = {"root_task": Task(id="t1", description="All clear", type=TaskType.REQUIREMENTS)}
    res = node(state, {})
    parsed = TypeAdapter(Clarifier.SCHEMA).validate_python(res)
    assert isinstance(parsed, ImplementedResponse)
