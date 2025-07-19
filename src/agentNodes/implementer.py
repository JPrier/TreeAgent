from typing import Any

from dataModel.task import Task
from dataModel.model_response import ImplementedResponse, ModelResponse

from .base import AgentNode


class Implementer(AgentNode):
    """Generates code artifacts."""

    SCHEMA = ImplementedResponse

    def execute_task(self, task: Task) -> ModelResponse:
        resp = ImplementedResponse(
            content="def foo(): pass",
            artifacts=["foo.py"],
        )
        return resp
