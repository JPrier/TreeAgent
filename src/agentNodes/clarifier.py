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

    PROMPT_TEMPLATE = (
        "You are checking if a project description needs any follow-up"
        " questions. If it is clear enough to begin work, respond with the"
        " phrase 'No clarification required'. Otherwise provide one concise"
        " question to ask.\nTask: {task}"
    )

    SCHEMA = FollowUpResponse | ImplementedResponse

    def __init__(self, llm_accessor: BaseModelAccessor):
        self.llm_accessor = llm_accessor

    def execute_task(self, task: Task) -> ModelResponse:
        result: ModelResponse = self.llm_accessor.call_model(
            prompt=Clarifier.PROMPT_TEMPLATE.format(task=task.description),
            schema=Clarifier.SCHEMA,
        )
        return result

    def __call__(self, task: Task, config: dict[str, Any] | None = None) -> dict:
        return self.execute_task(task).model_dump()
