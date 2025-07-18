from typing import Any

from modelAccessors.base_accessor import BaseModelAccessor
from dataModel.task import Task
from dataModel.model_response import ModelResponse, ImplementedResponse


class LLDDesigner:
    """Produces low-level design documentation."""

    PROMPT_TEMPLATE = (
        "Create a low level design based on the following description:\n"
        "{description}\n"
        "Complexity: {complexity}\n"
        "Return at most 5 subtasks using only the types: IMPLEMENT, RESEARCH, TEST."
    )

    SCHEMA = ImplementedResponse

    def __init__(self, llm_accessor: BaseModelAccessor):
        """Create the designer with the given model accessor."""
        self.llm_accessor = llm_accessor

    def execute_task(self, task: Task) -> ModelResponse:
        """Generate low level design details for ``task``."""
        prompt = LLDDesigner.PROMPT_TEMPLATE.format(
            description=task.description,
            complexity=task.complexity,
        )
        response: ModelResponse = self.llm_accessor.call_model(prompt, LLDDesigner.SCHEMA)
        return response

    def __call__(self, task: Task, config: dict[str, Any] | None = None) -> dict:
        """Execute and return a serialisable dict."""
        return self.execute_task(task).model_dump()
