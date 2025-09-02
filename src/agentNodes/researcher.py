from pydantic import TypeAdapter

from src.agentNodes.base_node import AgentNode
from src.modelAccessors.base_accessor import BaseModelAccessor
from src.dataModel.model_response import ImplementedResponse
from src.dataModel.task import Task

from src.tools.web_search import WEB_SEARCH_TOOL


class Researcher(AgentNode):
    """Gathers research artifacts using web search."""

    PROMPT_TEMPLATE = "{query}"
    ADAPTER = TypeAdapter(ImplementedResponse)
    SCHEMA = ADAPTER.json_schema()

    def __init__(self, llm_accessor: BaseModelAccessor):
        """Create the researcher with the given model accessor."""
        self.llm_accessor = llm_accessor

    def run_llm_agent(self, task: Task) -> ImplementedResponse:
        """Invoke the underlying LLM with the web search tool."""
        prompt = Researcher.PROMPT_TEMPLATE.format(query=task.description)
        return self.llm_accessor.call_model(
            prompt,
            model="researcher",
            system_prompt="You are a research assistant.",
            adapter=Researcher.ADAPTER,
            schema=Researcher.SCHEMA,
            tools=task.tools,
        )

    def execute_task(self, data: Task) -> ImplementedResponse:
        """Perform research for ``task`` using web search."""
        data.tools = [WEB_SEARCH_TOOL]
        return self.run_llm_agent(data)

