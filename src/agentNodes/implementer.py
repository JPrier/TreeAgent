from agentNodes.base_node import AgentNode
from dataModel.task import Task

from dataModel.model_response import ModelResponse, ImplementedResponse


class Implementer(AgentNode):
    """Generates code artifacts."""

    SCHEMA = ImplementedResponse

    def execute_task(self, task: Task) -> ModelResponse:
        """Return a stub implementation for ``task``."""
        resp = ImplementedResponse(
            content="def foo(): pass",
            artifacts=["foo.py"],
        )
        return resp
