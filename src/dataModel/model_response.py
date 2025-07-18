from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field
from .task import Task


class ModelResponseType(str, Enum):
    DECOMPOSED = "decomposed"
    IMPLEMENTED = "implemented"
    FOLLOW_UP_REQUIRED = "follow_up_required"
    FAILED = "failed"


class _BaseResponse(BaseModel):
    content: Optional[str] = None
    artifacts: list[str] = []


class DecomposedResponse(_BaseResponse):
    response_type: Literal[ModelResponseType.DECOMPOSED] = Field(
        default=ModelResponseType.DECOMPOSED
    )
    subtasks: list["Task"]


class ImplementedResponse(_BaseResponse):
    response_type: Literal[ModelResponseType.IMPLEMENTED] = Field(
        default=ModelResponseType.IMPLEMENTED
    )


class FollowUpResponse(_BaseResponse):
    response_type: Literal[ModelResponseType.FOLLOW_UP_REQUIRED] = Field(
        default=ModelResponseType.FOLLOW_UP_REQUIRED
    )
    follow_up_ask: "Task"


class FailedResponse(_BaseResponse):
    response_type: Literal[ModelResponseType.FAILED] = Field(
        default=ModelResponseType.FAILED
    )
    error_message: str
    retryable: bool = False


ModelResponse = Annotated[
    Union[DecomposedResponse, ImplementedResponse, FollowUpResponse, FailedResponse],
    Field(discriminator="response_type"),
]

Task.model_rebuild()
