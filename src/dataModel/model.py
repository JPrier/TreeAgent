from enum import Enum
from pydantic import BaseModel

class AccessorType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

class Model(BaseModel):
    name: str = "gpt-4.1-nano"  # Default to a reasonable OpenAI model
    accessor_type: AccessorType = AccessorType.OPENAI
