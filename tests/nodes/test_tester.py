from pydantic import TypeAdapter

from agentNodes.tester import Tester
from dataModel.model_response import ImplementedResponse


def test_tester_passed():
    node = Tester()
    res = node({}, {})
    parsed = TypeAdapter(Tester.SCHEMA).validate_python(res)
    assert isinstance(parsed, ImplementedResponse)
    assert parsed.content == "pytest passed"
