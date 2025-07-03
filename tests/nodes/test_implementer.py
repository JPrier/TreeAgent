from pydantic import TypeAdapter

from agentNodes.implementer import Implementer
from dataModel.model_response import ImplementedResponse


def test_implementer_returns_code():
    node = Implementer()
    res = node({}, {})
    parsed = TypeAdapter(Implementer.SCHEMA).validate_python(res)
    assert isinstance(parsed, ImplementedResponse)
    assert parsed.artifacts == ["foo.py"]
