from typing import Any

from modelAccessors.base_accessor import BaseModelAccessor

from dataModel.task import Task
from dataModel.model_response import (
    FollowUpResponse,
    ImplementedResponse,
    ModelResponse,
)


class Clarifier:
    """Decides whether the root task needs clarifying questions."""

    PROMPT_TEMPLATE = "Clarify the following task if needed: {task}"

    SCHEMA = FollowUpResponse | ImplementedResponse

    def __init__(self, llm_accessor: BaseModelAccessor):
        self.llm_accessor = llm_accessor

    def execute_task(self, task: Task) -> ModelResponse:
        result: ModelResponse = self.llm_accessor.call_model(
            prompt=Clarifier.PROMPT_TEMPLATE.format(task=task.description),
            schema=Clarifier.SCHEMA,
        )
        return result

    def __call__(self, state: dict[str, Any], config: dict[str, Any] | None = None) -> dict:
        root_task: Task = state["root_task"]
        return self.execute_task(root_task).model_dump()
