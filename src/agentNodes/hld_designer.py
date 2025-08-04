from src.agentNodes.base_node import AgentNode
from src.modelAccessors.base_accessor import BaseModelAccessor

from src.dataModel.task import Task
from src.dataModel.model_response import (
    ModelResponse,
    DecomposedResponse,
    ImplementedResponse,
)


class HLDDesigner(AgentNode):
    """Node that requests a high-level design from an LLM."""

    PROMPT_TEMPLATE = (
        "Create a high level design based on the following requirements:\n"
        "{requirements}\n"
        "Complexity: {complexity}\n"
        "Provide at most 5 subtasks using only the types: LLD, RESEARCH, TEST."
    )

    SCHEMA = DecomposedResponse | ImplementedResponse

    def __init__(self, llm_accessor: BaseModelAccessor):
        """Create the designer with the given model accessor."""
        self.llm_accessor = llm_accessor

    def execute_task(self, task: Task) -> ModelResponse:
        """Generate the high level design or subtasks for ``task``."""
        prompt = HLDDesigner.PROMPT_TEMPLATE.format(
            requirements=task.description,
            complexity=task.complexity,
        )
        response: ModelResponse = self.llm_accessor.call_model(prompt, HLDDesigner.SCHEMA)
        return response

