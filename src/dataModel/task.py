from enum import Enum
from pydantic import BaseModel
from typing import Optional, Dict, Any
from .model import Model

class TaskType(str, Enum):
    IMPLEMENT        = "implement"
    DESIGN           = "design"
    DECOMPOSE        = "decompose"
    RESEARCH         = "research"
    VALIDATE         = "validate"
    DOCUMENT         = "document"

class TaskStatus(str, Enum):
    PENDING             = "pending"
    IN_PROGRESS         = "in_progress"
    PENDING_VALIDATION  = "pending_validation"
    PENDING_USER_REVIEW = "pending_user_review"
    COMPLETED           = "completed"
    BLOCKED             = "blocked"
    FAILED              = "failed"

class Task(BaseModel):
    task_id:   str
    task_type: TaskType
    prompt:    str
    status:    TaskStatus = TaskStatus.PENDING
    model:     Model = Model()
    tools:     Optional[Dict[str, Any]] = None  # Available MCP tools for this task

    class Config:
        use_enum_values = True


