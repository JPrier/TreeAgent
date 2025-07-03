import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from agentNodes.researcher import Researcher
from dataModel.model_response import ImplementedResponse

import litellm

litellm.with_structured_output = lambda *a, **k: (lambda x: x)


def test_researcher_returns_artifact():
    node = Researcher()
    state = {}
    res = node(state, {})
    parsed = Researcher.SCHEMA.model_validate(res)
    assert isinstance(parsed, ImplementedResponse)
    assert parsed.artifacts == ["https://example.com"]
