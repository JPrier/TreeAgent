from pydantic import TypeAdapter

from src.agentNodes.reviewer import Reviewer
from src.dataModel.model_response import (
    ImplementedResponse,
    FailedResponse,
)


def test_reviewer_approves():
    node = Reviewer()
    last = ImplementedResponse(content="def foo(): pass", artifacts=["foo.py"])
    res = node({"last_response": last}, {})
    parsed = TypeAdapter(Reviewer.SCHEMA).validate_python(res)
    assert isinstance(parsed, ImplementedResponse)
    assert parsed.content == "LGTM"
    assert parsed.artifacts == ["foo.py"]


def test_reviewer_rejects():
    node = Reviewer()
    last = ImplementedResponse(content="print(1)", artifacts=["foo.py"])
    res = node({"last_response": last}, {})
    parsed = TypeAdapter(Reviewer.SCHEMA).validate_python(res)
    assert isinstance(parsed, FailedResponse)
    assert parsed.error_message == "Style error"
