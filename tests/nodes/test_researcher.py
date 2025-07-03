from pydantic import TypeAdapter
from agentNodes.researcher import Researcher
from dataModel.model_response import ImplementedResponse


def test_researcher_returns_artifact():
    node = Researcher()
    state = {}
    res = node(state, {})
    parsed = TypeAdapter(Researcher.SCHEMA).validate_python(res)
    assert isinstance(parsed, ImplementedResponse)
    assert parsed.artifacts == ["https://example.com"]
