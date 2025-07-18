from typing import Any

from dataModel.model_response import ImplementedResponse


class Deployer:
    """Deploys the final artifact."""

    SCHEMA = ImplementedResponse

    def __call__(self, state: dict[str, Any], config: dict[str, Any] | None = None) -> dict:
        """Return a stub deployment result."""
        last = state["last_response"]
        resp = ImplementedResponse(content="deployed", artifacts=last.artifacts)
        return resp.model_dump()
