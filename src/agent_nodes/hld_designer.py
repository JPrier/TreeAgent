from typing import Any

from dataModel.task import Task
from dataModel.model_response import (
    ModelResponse,
    DecomposedResponse,
    ImplementedResponse,
)


class HLDDesigner:
    """Node that requests a high-level design from an LLM."""

    PROMPT_TEMPLATE = (
        "Create a high level design based on the following requirements:\n"
        "{requirements}\n"
        "Complexity: {complexity}"
    )

    SCHEMA = DecomposedResponse | ImplementedResponse

    def __init__(self, llm_accessor: Any):
        self.llm_accessor = llm_accessor

    def execute_task(self, task: Task) -> ModelResponse:
        prompt = HLDDesigner.PROMPT_TEMPLATE.format(
            requirements=task.description,
            complexity=task.complexity,
        )
        response: ModelResponse = self.llm_accessor.call_model(
            prompt, HLDDesigner.SCHEMA
        )
        return response
