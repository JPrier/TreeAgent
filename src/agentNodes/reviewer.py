from typing import Any

from pydantic import TypeAdapter

from src.agentNodes.base_node import AgentNode
from src.dataModel.model_response import (
    ImplementedResponse,
    FailedResponse,
    TesterResponse,
)


class Reviewer(AgentNode):
    """Reviews implemented code and either approves or rejects."""

    ADAPTER: TypeAdapter[TesterResponse] = TypeAdapter(TesterResponse)
    SCHEMA = ADAPTER.json_schema()

    def execute_task(self, data: dict[str, Any]) -> TesterResponse:
        """Approve implementations that contain a ``def`` statement."""
        last = data["last_response"]
        content = last.content or ""
        resp: TesterResponse
        if "def" in content:
            resp = ImplementedResponse(content="LGTM", artifacts=last.artifacts)
        else:
            resp = FailedResponse(error_message="Style error")
        return resp
