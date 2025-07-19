from typing import Any

from dataModel.model_response import (
    ImplementedResponse,
    FailedResponse,
    ModelResponse,
)

from .base import AgentNode


class Reviewer(AgentNode):
    """Reviews implemented code and either approves or rejects."""

    SCHEMA = ImplementedResponse | FailedResponse

    def execute_task(self, state: dict[str, Any]) -> ModelResponse:
        last = state["last_response"]
        content = last.content or ""
        if "def" in content:
            resp = ImplementedResponse(content="LGTM", artifacts=last.artifacts)
        else:
            resp = FailedResponse(error_message="Style error")
        return resp
