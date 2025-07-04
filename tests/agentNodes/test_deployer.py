from pydantic import TypeAdapter

from agentNodes.deployer import Deployer
from dataModel.model_response import ImplementedResponse


def test_deployer_deploys():
    node = Deployer()
    last = ImplementedResponse(content="pytest passed", artifacts=["foo.py"])
    res = node({"last_response": last}, {})
    parsed = TypeAdapter(Deployer.SCHEMA).validate_python(res)
    assert isinstance(parsed, ImplementedResponse)
    assert parsed.content == "deployed"
    assert parsed.artifacts == ["foo.py"]
