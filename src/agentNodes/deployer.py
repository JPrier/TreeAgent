from typing import Any

from pydantic import TypeAdapter

from src.agentNodes.base_node import AgentNode
from src.dataModel.model_response import ImplementedResponse


class Deployer(AgentNode):
    """Deploys the final artifact."""

    ADAPTER = TypeAdapter(ImplementedResponse)
    SCHEMA = ADAPTER.json_schema()

    def execute_task(self, data: dict[str, Any]) -> ImplementedResponse:
        """Return a stub deployment result."""
        last = data["last_response"]
        resp = ImplementedResponse(content="deployed", artifacts=last.artifacts)
        return resp
