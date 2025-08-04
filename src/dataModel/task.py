from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator
from .model import Model

from src.modelAccessors.data.tool import Tool


class TaskType(str, Enum):
    REQUIREMENTS = "requirements"
    RESEARCH = "research"
    HLD = "hld"
    LLD = "lld"
    IMPLEMENT = "implement"
    REVIEW = "review"
    TEST = "test"
    JURY = "jury"
    DEPLOY = "deploy"


class TaskStatus(str, Enum):
    """Lifecycle state for a task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PENDING_VALIDATION = "pending_validation"
    PENDING_USER_REVIEW = "pending_user_review"
    PENDING_USER_INPUT = "pending_user_input"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


class Task(BaseModel):
    """Basic unit of work for the agent tree."""

    id: str
    description: str
    type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    complexity: int = 1
    parent_id: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    tools: list[Tool] = Field(default_factory=list)
    model: Model = Field(default_factory=Model)
    result: Optional[str] = None

    @model_validator(mode="after")
    def _validate_complexity(self) -> "Task":
        if self.complexity < 1:
            raise ValueError("complexity must be >= 1")
        return self


