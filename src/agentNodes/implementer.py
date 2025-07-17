from typing import Any

from dataModel.task import Task

from dataModel.model_response import ImplementedResponse


class Implementer:
    """Generates code artifacts."""

    SCHEMA = ImplementedResponse

    def __call__(self, task: Task, config: dict[str, Any] | None = None) -> dict:
        resp = ImplementedResponse(
            content="def foo(): pass",
            artifacts=["foo.py"],
        )
        return resp.model_dump()
