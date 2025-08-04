from src.agentNodes.base_node import AgentNode
from src.modelAccessors.base_accessor import BaseModelAccessor
from src.dataModel.task import Task
from src.dataModel.model_response import ModelResponse, ImplementedResponse


class LLDDesigner(AgentNode):
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

