from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List

from pydantic import BaseModel, Field

class Tool(BaseModel):
    """Definition of a tool that can be used by a model."""

    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

class BaseModelAccessor(ABC):
    @abstractmethod
    def prompt_model(self, model: str, system_prompt: str, user_prompt: str) -> Any:
        """Basic text prompting with no tools"""
        pass

    @abstractmethod
    def execute_task_with_tools(self, model: str, system_prompt: str, user_prompt: str, tools: Optional[List[Tool]] = None) -> Any:
        """
        Execute a task with available tools. The accessor handles whether to:
        1. Use native tool calling (for agentic models)
        2. Simulate tool execution through chat (for chat-only models)
        """
        pass

    def supports_tools(self, model: str) -> bool:
        """Check if a model supports native tool use"""
        return False
