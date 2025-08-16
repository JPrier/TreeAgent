from abc import ABC, abstractmethod
from typing import Any, Optional

from .data.tool import Tool

class BaseModelAccessor(ABC):
    @abstractmethod
    def prompt_model(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        schema,
    ) -> Any:
        """Basic text prompting with no tools"""
        pass

    @abstractmethod
    def call_model(self, prompt: str, schema) -> Any:
        """Simpler helper for tests and lightweight callers"""
        pass

    @abstractmethod
    def execute_task_with_tools(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        schema,
        tools: Optional[list[Tool]] = None,
    ) -> Any:
        """
        Execute a task with available tools. The accessor handles whether to:
        1. Use native tool calling (for agentic models)
        2. Simulate tool execution through chat (for chat-only models)
        """
        pass

    def supports_tools(self, model: str) -> bool:
        """Check if a model supports native tool use"""
        return False
