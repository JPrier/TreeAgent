from src.agentNodes.base_node import AgentNode
from src.modelAccessors.base_accessor import BaseModelAccessor

from src.dataModel.task import Task
from src.dataModel.model_response import (
    FollowUpResponse,
    ImplementedResponse,
    ModelResponse,
)


class Clarifier(AgentNode):
    """Decides whether the root task needs clarifying questions."""

    PROMPT_TEMPLATE = (
        "You are checking if a project description needs any follow-up"
        " questions. If it is clear enough to begin work, respond with the"
        " phrase 'No clarification required'. Otherwise provide one concise"
        " question to ask.\nTask: {task}"
    )

    SCHEMA = FollowUpResponse | ImplementedResponse

    def __init__(self, llm_accessor: BaseModelAccessor):
        """Create a Clarifier.

        Parameters
        ----------
        llm_accessor:
            Model accessor used to query the language model.
        """
        self.llm_accessor = llm_accessor

    def execute_task(self, task: Task) -> ModelResponse:
        """Ask the LLM whether the requirements need clarification."""
        result: ModelResponse = self.llm_accessor.call_model(
            prompt=Clarifier.PROMPT_TEMPLATE.format(task=task.description),
            schema=Clarifier.SCHEMA,
        )
        return result

