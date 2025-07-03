from typing import Any, Dict

from dataModel.model_response import ImplementedResponse


class Deployer:
    """Deploys the final artifact."""

    SCHEMA = ImplementedResponse

    def __call__(self, state: Dict[str, Any], config: Dict[str, Any] | None = None) -> dict:
        last = state["last_response"]
        resp = ImplementedResponse(content="deployed", artifacts=last.artifacts)
        return resp.model_dump()
