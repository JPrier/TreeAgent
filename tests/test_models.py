import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

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
