from pydantic import TypeAdapter

from src.agentNodes.base_node import AgentNode
from src.modelAccessors.base_accessor import BaseModelAccessor
from src.dataModel.task import Task

from src.dataModel.model_response import TesterResponse


class Tester(AgentNode):
    """Runs tests on the implementation using an LLM accessor."""

    PROMPT_TEMPLATE = (
        "You are a software tester. Review the following implementation or "
        "description and provide a short test result summary.\n{description}\n"
        "Respond with JSON matching the ImplementedResponse schema."
    )

    ADAPTER = TypeAdapter(TesterResponse)
    SCHEMA = ADAPTER.json_schema()

    def __init__(self, llm_accessor: BaseModelAccessor) -> None:
        self.llm_accessor = llm_accessor

    def execute_task(self, data: Task | None = None) -> TesterResponse:
        """Return test results for ``task`` using the LLM accessor."""
        desc = data.description if data else ""
        prompt = Tester.PROMPT_TEMPLATE.format(description=desc)
        return self.llm_accessor.call_model(
            prompt,
            adapter=Tester.ADAPTER,
            schema=Tester.SCHEMA,
        )
