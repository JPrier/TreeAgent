from pydantic import TypeAdapter

from agentNodes.lld_designer import LLDDesigner
from dataModel.model_response import ImplementedResponse


def test_lld_designer_returns_doc():
    node = LLDDesigner()
    res = node({}, {})
    parsed = TypeAdapter(LLDDesigner.SCHEMA).validate_python(res)
    assert isinstance(parsed, ImplementedResponse)
    assert parsed.content.startswith("LLD")
