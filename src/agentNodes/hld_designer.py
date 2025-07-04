from types import SimpleNamespace
from typing import Any, Dict

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

    def __init__(self, llm_accessor: Any | None = None):
        # allow tests to pass in a stub accessor; default returns a simple outline
        if llm_accessor is None:
            llm_accessor = SimpleNamespace(
                call_model=lambda prompt, schema: ImplementedResponse(content="outline")
            )
        self.llm_accessor = llm_accessor

    def execute_task(self, task: Task) -> ModelResponse:
        prompt = HLDDesigner.PROMPT_TEMPLATE.format(
            requirements=task.description,
            complexity=task.complexity,
        )
        response: ModelResponse = self.llm_accessor.call_model(prompt, HLDDesigner.SCHEMA)
        return response

    def __call__(self, state: Dict[str, Any], config: Dict[str, Any] | None = None) -> dict:
        current_task: Task = state["task_queue"][0]
        return self.execute_task(current_task).model_dump()
