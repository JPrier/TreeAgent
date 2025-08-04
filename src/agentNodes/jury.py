from __future__ import annotations

from src.agentNodes.base_node import AgentNode
from src.dataModel.model_response import ImplementedResponse, ModelResponse
from src.dataModel.task import Task
from src.modelAccessors.base_accessor import BaseModelAccessor


class Jury(AgentNode):
    """Evaluates sibling subtasks and records a verdict.

    This minimal implementation simply acknowledges that an evaluation
    occurred. More complex logic will be added in future iterations.
    """

    SCHEMA = ImplementedResponse

    def __init__(self, accessor: BaseModelAccessor) -> None:
        self.accessor = accessor

    def execute_task(self, task: Task | None = None) -> ModelResponse:
        """Return a placeholder verdict for ``task``."""
        return ImplementedResponse(content="jury verdict")
