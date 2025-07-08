from typing import Any, Dict

from pydantic import BaseModel, Field


class Tool(BaseModel):
    """Definition of a tool that can be used by a model."""

    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
