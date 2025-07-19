from typing import Any

from dataModel.model_response import ImplementedResponse, ModelResponse

from .base import AgentNode


class Deployer(AgentNode):
    """Deploys the final artifact."""

    SCHEMA = ImplementedResponse

    def execute_task(self, state: dict[str, Any]) -> ModelResponse:
        last = state["last_response"]
        resp = ImplementedResponse(content="deployed", artifacts=last.artifacts)
        return resp
