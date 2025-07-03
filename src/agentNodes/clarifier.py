from typing import Any, Dict

from dataModel.task import Task, TaskType
from dataModel.model_response import FollowUpResponse, ImplementedResponse


class Clarifier:
    """Decides whether the root task needs clarifying questions."""

    SCHEMA = FollowUpResponse | ImplementedResponse

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

        return resp.model_dump()
