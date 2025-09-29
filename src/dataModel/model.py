from enum import Enum
from pydantic import BaseModel

class AccessorType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GITHUB_COPILOT = "github_copilot"
    MOCK = "mock"

class Model(BaseModel):
    name: str = "gpt-5-nano"
    accessor_type: AccessorType = AccessorType.MOCK
