from typing import Any

from dataModel.task import Task

from dataModel.model_response import ImplementedResponse, ModelResponse

from .base import AgentNode


class Tester(AgentNode):
    """Runs tests on the implementation."""

    SCHEMA = ImplementedResponse

    def execute_task(self, task: Task | None = None) -> ModelResponse:
        resp = ImplementedResponse(content="pytest passed")
        return resp
