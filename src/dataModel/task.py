from enum import Enum
from pydantic import BaseModel
from typing import Optional, Dict, Any
from .model import Model

class TaskType(str, Enum):
    IMPLEMENT_CODE   = "implement_code"
    DESIGN_SYSTEM    = "design_system"
    DESIGN_CODE      = "design_code"
    DECOMPOSE        = "decompose"
    RESEARCH_WEB     = "research_web"
    RESEARCH_CODE    = "research_code"
    VALIDATE_CODE    = "validate_code"
    VALIDATE_DESIGN  = "validate_design"
    DOCUMENT         = "document"
    UNKNOWN          = "unknown"

class TaskStatus(str, Enum):
    PENDING             = "pending"
    IN_PROGRESS         = "in_progress"
    PENDING_VALIDATION  = "pending_validation"
    PENDING_USER_REVIEW = "pending_user_review"
    PENDING_USER_INPUT  = "pending_user_input"
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
    result:    Optional[str] = None  # Result of the task execution

    class Config:
        use_enum_values = True

# TODO: Map MCP tools to TaskTypes -- How can I do this dynamically so users can use any MCP servers
TOOL_SET: dict[TaskType, str] = {

}


