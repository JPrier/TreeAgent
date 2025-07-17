from __future__ import annotations

from pydantic import BaseModel

from .task import Task


class Project(BaseModel):
    """Container for tasks and their execution state."""

    rootTask: Task
    failedTasks: list[Task]
    completedTasks: list[Task]
    inProgressTasks: list[Task]
    queuedTasks: list[Task]
