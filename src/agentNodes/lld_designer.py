from typing import Any, Dict

from modelAccessors.base_accessor import BaseModelAccessor
from dataModel.task import Task
from dataModel.model_response import ModelResponse, ImplementedResponse


class LLDDesigner:
    """Produces low-level design documentation."""

    PROMPT_TEMPLATE = (
        "Create a low level design based on the following description:\n"
        "{description}\n"
        "Complexity: {complexity}"
    )

    SCHEMA = ImplementedResponse

    def __init__(self, llm_accessor: BaseModelAccessor):
        self.llm_accessor = llm_accessor

    def execute_task(self, task: Task) -> ModelResponse:
        prompt = LLDDesigner.PROMPT_TEMPLATE.format(
            description=task.description,
            complexity=task.complexity,
        )
        response: ModelResponse = self.llm_accessor.call_model(prompt, LLDDesigner.SCHEMA)
        return response

    def __call__(self, state: Dict[str, Any], config: Dict[str, Any] | None = None) -> dict:
        current_task: Task = state["task_queue"][0]
        return self.execute_task(current_task).model_dump()
