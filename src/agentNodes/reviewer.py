from typing import Any, Dict

from dataModel.model_response import ImplementedResponse, FailedResponse


class Reviewer:
    """Reviews implemented code and either approves or rejects."""

    SCHEMA = ImplementedResponse | FailedResponse

    def __call__(self, state: Dict[str, Any], config: Dict[str, Any] | None = None) -> dict:
        last = state["last_response"]
        content = last.content or ""
        if "def" in content:
            resp = ImplementedResponse(content="LGTM", artifacts=last.artifacts)
        else:
            resp = FailedResponse(error_message="Style error")
        return resp.model_dump()
