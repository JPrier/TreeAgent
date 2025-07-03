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


class HLDDesigner:
    """Creates high-level design subtasks or a simple outline."""

    SCHEMA = TypeAdapter(DecomposedResponse | ImplementedResponse)
    SCHEMA.model_validate = SCHEMA.validate_python

    def __call__(self, state: Dict[str, Any], config: Dict[str, Any] | None = None) -> dict:
        task_queue = state["task_queue"]
        current_task: Task = task_queue[0]
        if current_task.complexity > 1:
            subtasks = [
                Task(
                    id=f"{current_task.id}-{i+1}",
                    description=f"HLD step {i+1}",
                    type=TaskType.HLD,
                    complexity=1,
                    parent_id=current_task.id,
                )
                for i in range(current_task.complexity)
            ]
            resp = DecomposedResponse(subtasks=subtasks)
        else:
            resp = ImplementedResponse(content="HLD outline ...")

        _ = with_structured_output(self.SCHEMA)
        return resp.model_dump()
