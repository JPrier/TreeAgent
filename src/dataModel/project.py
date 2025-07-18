from __future__ import annotations

from pydantic import BaseModel, Field

from .model_response import ModelResponse

from .task import Task


class Project(BaseModel):
    """Container for tasks and their execution state."""

    rootTask: Task
    failedTasks: list[Task]
    completedTasks: list[Task]
    inProgressTasks: list[Task]
    queuedTasks: list[Task]
    taskResults: dict[str, ModelResponse] = Field(default_factory=dict)
    latestResponse: ModelResponse | None = None
