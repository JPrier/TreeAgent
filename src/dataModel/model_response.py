from enum import Enum
from typing import Literal, Annotated, Union
from pydantic import BaseModel, Field
from src.dataModel.task import Task

class ModelResponseType(str, Enum):
    DECOMPOSED = "decomposed"
    IMPLEMENTED = "implemented"
    FAILED      = "failed"

class DecomposedResponse(BaseModel):
    response_type: Literal[ModelResponseType.DECOMPOSED] = Field(default=ModelResponseType.DECOMPOSED)
    subtasks: list[Task]

class ImplementedResponse(BaseModel):
    response_type: Literal[ModelResponseType.IMPLEMENTED] = Field(default=ModelResponseType.IMPLEMENTED)
    summary: str

class FailedResponse(BaseModel):
    response_type: Literal[ModelResponseType.FAILED] = Field(default=ModelResponseType.FAILED)
    error_message: str
    retryable: bool

ModelResponse = Annotated[
    Union[DecomposedResponse, ImplementedResponse, FailedResponse],
    Field(discriminator="response_type")
]
