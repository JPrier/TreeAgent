from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal, Optional, TypeAlias, Union

from .task import Task

from pydantic import BaseModel, Field


class _BaseResponse(BaseModel):
    content: Optional[str] = None
    artifacts: list[str] = []
    model_config = {"extra": "forbid"}


class ModelResponseType(str, Enum):
    DECOMPOSED = "decomposed"
    IMPLEMENTED = "implemented"
    FOLLOW_UP_REQUIRED = "follow_up_required"
    FAILED = "failed"


class DecomposedResponse(_BaseResponse):
    type: Literal[ModelResponseType.DECOMPOSED] = Field(
        default=ModelResponseType.DECOMPOSED
    )
    subtasks: list[Task]


class ImplementedResponse(_BaseResponse):
    type: Literal[ModelResponseType.IMPLEMENTED] = Field(
        default=ModelResponseType.IMPLEMENTED
    )


class FollowUpResponse(_BaseResponse):
    type: Literal[ModelResponseType.FOLLOW_UP_REQUIRED] = Field(
        default=ModelResponseType.FOLLOW_UP_REQUIRED
    )
    follow_up_ask: Task


class FailedResponse(_BaseResponse):
    type: Literal[ModelResponseType.FAILED] = Field(
        default=ModelResponseType.FAILED
    )
    error_message: str
    retryable: bool = False


ModelResponse: TypeAlias = Annotated[
    Union[DecomposedResponse, ImplementedResponse, FollowUpResponse, FailedResponse],
    Field(discriminator="type"),
]

ClarifierResponse: TypeAlias = Annotated[
    Union[FollowUpResponse, ImplementedResponse],
    Field(discriminator="type"),
]

DesignerResponse: TypeAlias = Annotated[
    Union[DecomposedResponse, ImplementedResponse],
    Field(discriminator="type"),
]

TesterResponse: TypeAlias = Annotated[
    Union[ImplementedResponse, FailedResponse],
    Field(discriminator="type"),
]

