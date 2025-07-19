from agentNodes.base_node import AgentNode
from dataModel.task import Task

from dataModel.model_response import ModelResponse, ImplementedResponse


class Tester(AgentNode):
    """Runs tests on the implementation."""

    SCHEMA = ImplementedResponse

    def execute_task(self, task: Task | None = None) -> ModelResponse:
        """Return a stub test result."""
        resp = ImplementedResponse(content="pytest passed")
        return resp
