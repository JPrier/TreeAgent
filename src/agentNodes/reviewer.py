from typing import Any

from agentNodes.base_node import AgentNode
from dataModel.model_response import (
    ImplementedResponse,
    FailedResponse,
    ModelResponse,
)


class Reviewer(AgentNode):
    """Reviews implemented code and either approves or rejects."""

    SCHEMA = ImplementedResponse | FailedResponse

    def execute_task(self, state: dict[str, Any]) -> ModelResponse:
        """Approve implementations that contain a ``def`` statement."""
        last = state["last_response"]
        content = last.content or ""
        if "def" in content:
            resp = ImplementedResponse(content="LGTM", artifacts=last.artifacts)
        else:
            resp = FailedResponse(error_message="Style error")
        return resp
