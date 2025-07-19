from typing import Any

from dataModel.task import Task

from dataModel.model_response import ImplementedResponse


class Tester:
    """Runs tests on the implementation."""

    SCHEMA = ImplementedResponse

    def __call__(self, task: Task | None = None, config: dict[str, Any] | None = None) -> dict:
        """Return a stub test result."""
        resp = ImplementedResponse(content="pytest passed")
        return resp.model_dump()
