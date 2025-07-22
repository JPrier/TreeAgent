from agentNodes.base_node import AgentNode
from modelAccessors.base_accessor import BaseModelAccessor
from dataModel.task import Task

from dataModel.model_response import ModelResponse, ImplementedResponse, FailedResponse


class Tester(AgentNode):
    """Runs tests on the implementation using an LLM accessor."""

    PROMPT_TEMPLATE = (
        "You are a software tester. Review the following implementation or "
        "description and provide a short test result summary.\n{description}\n"
        "Respond with JSON matching the ImplementedResponse schema."
    )

    SCHEMA = ImplementedResponse | FailedResponse

    def __init__(self, llm_accessor: BaseModelAccessor) -> None:
        self.llm_accessor = llm_accessor

    def execute_task(self, task: Task | None = None) -> ModelResponse:
        """Return test results for ``task`` using the LLM accessor."""
        desc = task.description if task else ""
        prompt = Tester.PROMPT_TEMPLATE.format(description=desc)
        response: ModelResponse = self.llm_accessor.call_model(prompt, Tester.SCHEMA)
        return response
