from typing import Any, Dict

from dataModel.model_response import ImplementedResponse


class LLDDesigner:
    """Produces low-level design documentation."""

    SCHEMA = ImplementedResponse

    def __call__(self, state: Dict[str, Any], config: Dict[str, Any] | None = None) -> dict:
        resp = ImplementedResponse(content="LLD doc ...")
        return resp.model_dump()
