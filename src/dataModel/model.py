from enum import Enum
from pydantic import BaseModel

class AccessorType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOCK = "mock"

class Model(BaseModel):
    name: str = "gpt-4.1-nano"
    accessor_type: AccessorType = AccessorType.MOCK
