from typing import cast

from pydantic import TypeAdapter

from src.agentNodes.base_node import AgentNode
from src.modelAccessors.base_accessor import BaseModelAccessor

from src.dataModel.task import Task
from src.dataModel.model_response import ClarifierResponse, ModelResponse


class Clarifier(AgentNode):
    """Decides whether the root task needs clarifying questions."""

    PROMPT_TEMPLATE = (
        "You are checking if a project description needs any follow-up"
        " questions. If it is clear enough to begin work, respond with the"
        " phrase 'No clarification required'. Otherwise provide one concise"
        " question to ask.\nTask: {task}"
    )

    ADAPTER: TypeAdapter[ModelResponse] = cast(
        TypeAdapter[ModelResponse], TypeAdapter(ClarifierResponse)
    )
    SCHEMA = ADAPTER.json_schema()

    def __init__(self, llm_accessor: BaseModelAccessor):
        """Create a Clarifier.

        Parameters
        ----------
        llm_accessor:
            Model accessor used to query the language model.
        """
        self.llm_accessor = llm_accessor

    def execute_task(self, data: Task) -> ClarifierResponse:
        """Ask the LLM whether the requirements need clarification."""
        resp = self.llm_accessor.call_model(
            prompt=Clarifier.PROMPT_TEMPLATE.format(task=data.description),
            adapter=Clarifier.ADAPTER,
            schema=Clarifier.SCHEMA,
        )
        return cast(ClarifierResponse, resp)

