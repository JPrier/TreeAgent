from src.agentNodes.base_node import AgentNode
from src.modelAccessors.base_accessor import BaseModelAccessor
from src.dataModel.model_response import ModelResponse, ImplementedResponse
from src.dataModel.task import Task

from src.tools.web_search import WEB_SEARCH_TOOL


class Researcher(AgentNode):
    """Gathers research artifacts using web search."""

    PROMPT_TEMPLATE = "{query}"
    SCHEMA = ImplementedResponse

    def __init__(self, llm_accessor: BaseModelAccessor):
        """Create the researcher with the given model accessor."""
        self.llm_accessor = llm_accessor

    def run_llm_agent(self, task: Task) -> ModelResponse:
        """Invoke the underlying LLM with the web search tool."""
        prompt = Researcher.PROMPT_TEMPLATE.format(query=task.description)
        return self.llm_accessor.execute_task_with_tools(
            model="researcher",
            system_prompt="You are a research assistant.",
            user_prompt=prompt,
            tools=task.tools,
        )

    def execute_task(self, data: Task) -> ModelResponse:
        """Perform research for ``task`` using web search."""
        data.tools = [WEB_SEARCH_TOOL]
        result: ModelResponse = self.run_llm_agent(data)
        return result

