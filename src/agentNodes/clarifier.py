from typing import Any, Dict

from pydantic import TypeAdapter
from dataModel.task import Task, TaskType
from dataModel.model_response import (
    FollowUpResponse,
    ImplementedResponse,
    DecomposedResponse,
    ModelResponse,
)

from litellm import with_structured_output


class Clarifier:
    """Decides whether the root task needs clarifying questions."""

    SCHEMA = TypeAdapter(FollowUpResponse | ImplementedResponse)
    SCHEMA.model_validate = SCHEMA.validate_python  # for convenience

    def __call__(self, state: Dict[str, Any], config: Dict[str, Any] | None = None) -> dict:
        root_task: Task = state["root_task"]
        if root_task.description.strip().endswith("?"):
            resp = FollowUpResponse(
                follow_up_ask=Task(
                    id=f"{root_task.id}-followup",
                    description="Need more details",
                    type=TaskType.REQUIREMENTS,
                    complexity=1,
                )
            )
        else:
            resp = ImplementedResponse(content="Requirements already clear")

        _ = with_structured_output(self.SCHEMA)
        return resp.model_dump()
