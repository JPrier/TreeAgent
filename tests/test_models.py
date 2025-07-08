import pytest
from pydantic import ValidationError

from dataModel import (
    Task,
    TaskType,
    DecomposedResponse,
    ImplementedResponse,
    FollowUpResponse,
    FailedResponse,
)
from tools.web_search import WEB_SEARCH_TOOL


def build_task(task_id: str = "t1") -> Task:
    return Task(id=task_id, description="desc", type=TaskType.HLD)


def test_task_type_enum_invariance():
    assert TaskType("hld") is TaskType.HLD


def test_task_complexity_validation():
    with pytest.raises(ValidationError):
        Task(id="bad", description="d", type=TaskType.HLD, complexity=0)


@pytest.mark.parametrize(
    "cls, kwargs, tag",
    [
        (DecomposedResponse, {"subtasks": [build_task("sub")]}, "decomposed"),
        (ImplementedResponse, {}, "implemented"),
        (
            FollowUpResponse,
            {"follow_up_ask": build_task("follow")},
            "follow_up_required",
        ),
        (FailedResponse, {"error_message": "oops"}, "failed"),
    ],
)
def test_model_response_round_trip_and_discriminator(cls, kwargs, tag):
    orig = cls(**kwargs)
    packed = orig.model_dump()
    restored = cls.model_validate(packed)
    assert restored == orig
    assert packed["response_type"] == tag


def test_task_allows_tools():
    task = Task(id="tool", description="d", type=TaskType.RESEARCH, tools=[WEB_SEARCH_TOOL])
    assert task.tools == [WEB_SEARCH_TOOL]
