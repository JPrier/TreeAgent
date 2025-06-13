from enum import Enum
from pydantic import BaseModel, Field
from src.dataModel.task import TaskModel
from typing import Annotated, Union

class ModelResponseType(str, Enum):
    DECOMPOSED = "decomposed"
    IMPLEMENTED = "implemented"
    FAILED      = "failed"

class DecomposedResponse(BaseModel):
    response_type: ModelResponseType = Field(ModelResponseType.DECOMPOSED, const=True)
    subtasks: list[TaskModel]

class ImplementedResponse(BaseModel):
    response_type: ModelResponseType = Field(ModelResponseType.IMPLEMENTED, const=True)
    summary: str

class FailedResponse(BaseModel):
    response_type: ModelResponseType = Field(ModelResponseType.FAILED, const=True)
    error_message: str
    retryable: bool

ModelResponse = Annotated[
    Union[
        DecomposedResponse,
        ImplementedResponse,
        FailedResponse,
    ],
    Field(discriminator="response_type")
]