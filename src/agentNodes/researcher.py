from typing import Any, Dict

from pydantic import TypeAdapter
from dataModel.task import Task, TaskType
from dataModel.model_response import (
    FollowUpResponse,
    ImplementedResponse,
    DecomposedResponse,
    ModelResponse,
)

from litellm import with_structured_output


class Researcher:
    """Gathers research artifacts for a task."""

    SCHEMA = TypeAdapter(ImplementedResponse)
    SCHEMA.model_validate = SCHEMA.validate_python

    def __call__(self, state: Dict[str, Any], config: Dict[str, Any] | None = None) -> dict:
        resp = ImplementedResponse(artifacts=["https://example.com"])
        _ = with_structured_output(self.SCHEMA)
        return resp.model_dump()
