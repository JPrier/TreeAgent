from agentNodes.base_node import AgentNode
from modelAccessors.base_accessor import BaseModelAccessor
from dataModel.task import Task

from dataModel.model_response import ModelResponse, ImplementedResponse


class Implementer(AgentNode):
    """Generates code artifacts using an LLM accessor."""

    PROMPT_TEMPLATE = (
        "Generate python code based on the following description:\n"
        "{description}\n"
        "Respond with JSON matching the ImplementedResponse schema "
        "summarising the implementation and listing any file names."
    )

    SCHEMA = ImplementedResponse

    def __init__(self, llm_accessor: BaseModelAccessor) -> None:
        """Create the implementer with the given accessor."""
        self.llm_accessor = llm_accessor

    def execute_task(self, task: Task) -> ModelResponse:
        """Generate code for ``task`` using the LLM accessor."""
        prompt = Implementer.PROMPT_TEMPLATE.format(description=task.description)
        response: ModelResponse = self.llm_accessor.call_model(prompt, Implementer.SCHEMA)
        return response
