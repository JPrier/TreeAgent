from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class Phase(str, Enum):
    """Project phases."""

    REQUIREMENTS = "requirements"
    RESEARCH = "research"
    HLD = "hld"
    LLD = "lld"
    IMPLEMENT = "implement"
    REVIEW = "review"
    TEST = "test"
    DEPLOY = "deploy"


class Task(BaseModel):
    """A unit of work executed by the agent tree."""

    id: str
    description: str
    phase: Phase
    complexity: int = 1
    parent_id: Optional[str] = None
    metadata: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_complexity(cls, data: "Task") -> "Task":
        if data.complexity < 1:
            raise ValueError("complexity must be >= 1")
        return data

