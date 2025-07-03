from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field

from .task import Task


class _BaseResponse(BaseModel):
    content: Optional[str] = None
    artifacts: list[str] = []


class DecomposedResponse(_BaseResponse):
    response_type: Literal["decomposed"] = Field("decomposed")
    subtasks: list[Task]


class ImplementedResponse(_BaseResponse):
    response_type: Literal["implemented"] = Field("implemented")


class FollowUpResponse(_BaseResponse):
    response_type: Literal["follow_up_required"] = Field("follow_up_required")
    follow_up_ask: Task


class FailedResponse(_BaseResponse):
    response_type: Literal["failed"] = Field("failed")
    error_message: str
    retryable: bool = False


ModelResponse = Annotated[
    Union[DecomposedResponse, ImplementedResponse, FollowUpResponse, FailedResponse],
    Field(discriminator="response_type"),
]
