from typing import Any, Dict

from modelAccessors.base_accessor import BaseModelAccessor
from dataModel.model_response import ModelResponse, ImplementedResponse
from dataModel.task import Task

from tools.web_search import WEB_SEARCH_TOOL


class Researcher:
    """Gathers research artifacts using web search."""

    PROMPT_TEMPLATE = "{query}"
    SCHEMA = ImplementedResponse

    def __init__(self, llm_accessor: BaseModelAccessor):
        self.llm_accessor = llm_accessor

    def run_llm_agent(self, task: Task) -> ModelResponse:
        prompt = Researcher.PROMPT_TEMPLATE.format(query=task.description)
        return self.llm_accessor.execute_task_with_tools(
            model="researcher",
            system_prompt="You are a research assistant.",
            user_prompt=prompt,
            tools=task.tools,
        )

    def execute_task(self, task: Task) -> ModelResponse:
        task.tools = [WEB_SEARCH_TOOL]
        result: ModelResponse = self.run_llm_agent(task)
        return result

    def __call__(self, state: Dict[str, Any], config: Dict[str, Any] | None = None) -> dict:
        current_task: Task = state["task_queue"][0]
        return self.execute_task(current_task).model_dump()
