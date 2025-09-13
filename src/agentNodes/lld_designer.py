from typing import cast

from pydantic import TypeAdapter

from src.agentNodes.base_node import AgentNode
from src.modelAccessors.base_accessor import BaseModelAccessor
from src.dataModel.task import Task
from src.dataModel.model_response import ImplementedResponse, ModelResponse


class LLDDesigner(AgentNode):
    """Produces low-level design documentation."""

    PROMPT_TEMPLATE = (
        "Create a low level design based on the following description:\n"
        "{description}\n"
        "Complexity: {complexity}\n"
        "Return at most 5 subtasks using only the types: IMPLEMENT, RESEARCH, TEST."
    )

    ADAPTER: TypeAdapter[ModelResponse] = cast(
        TypeAdapter[ModelResponse], TypeAdapter(ImplementedResponse)
    )
    SCHEMA = ADAPTER.json_schema()

    def __init__(self, llm_accessor: BaseModelAccessor):
        """Create the designer with the given model accessor."""
        self.llm_accessor = llm_accessor

    def execute_task(self, data: Task) -> ImplementedResponse:
        """Generate low level design details for ``task``."""
        prompt = LLDDesigner.PROMPT_TEMPLATE.format(
            description=data.description,
            complexity=data.complexity,
        )
        resp = self.llm_accessor.call_model(
            prompt,
            adapter=LLDDesigner.ADAPTER,
            schema=LLDDesigner.SCHEMA,
        )
        return cast(ImplementedResponse, resp)

