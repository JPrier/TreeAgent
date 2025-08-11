from typing import Any

from src.agentNodes.base_node import AgentNode
from src.dataModel.model_response import ImplementedResponse, ModelResponse


class Deployer(AgentNode):
    """Deploys the final artifact."""

    SCHEMA = ImplementedResponse

    def execute_task(self, data: dict[str, Any]) -> ModelResponse:
        """Return a stub deployment result."""
        last = data["last_response"]
        resp = ImplementedResponse(content="deployed", artifacts=last.artifacts)
        return resp
