import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from agentNodes.clarifier import Clarifier
from dataModel.task import Task, TaskType
from dataModel.model_response import FollowUpResponse, ImplementedResponse

import litellm

litellm.with_structured_output = lambda *a, **k: (lambda x: x)


def test_clarifier_followup():
    node = Clarifier()
    state = {"root_task": Task(id="t1", description="Need specs?", type=TaskType.REQUIREMENTS)}
    res = node(state, {})
    parsed = Clarifier.SCHEMA.model_validate(res)
    assert isinstance(parsed, FollowUpResponse)


def test_clarifier_implemented():
    node = Clarifier()
    state = {"root_task": Task(id="t1", description="All clear", type=TaskType.REQUIREMENTS)}
    res = node(state, {})
    parsed = Clarifier.SCHEMA.model_validate(res)
    assert isinstance(parsed, ImplementedResponse)
