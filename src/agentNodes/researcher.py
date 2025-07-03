from typing import Any, Dict

from dataModel.model_response import ImplementedResponse


class Researcher:
    """Gathers research artifacts for a task."""

    SCHEMA = ImplementedResponse

    def __call__(self, state: Dict[str, Any], config: Dict[str, Any] | None = None) -> dict:
        resp = ImplementedResponse(artifacts=["https://example.com"])
        return resp.model_dump()
