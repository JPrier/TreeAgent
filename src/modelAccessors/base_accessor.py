from abc import ABC, abstractmethod
from typing import Any, Optional, Dict

class BaseModelAccessor(ABC):
    @abstractmethod
    def prompt_model(self, model: str, system_prompt: str, user_prompt: str):
        pass

    @abstractmethod
    def execute_task_with_tools(self, model: str, system_prompt: str, user_prompt: str, tools: Optional[Dict[str, Any]] = None):
        """
        Execute a task with available MCP tools. The accessor handles whether to:
        1. Use native tool calling (for agentic models)
        2. Simulate tool execution through chat (for chat-only models)
        """
        pass

    def supports_mcp(self, model: str) -> bool:
        """Return True if this model supports direct MCP commands."""
        return False

    def run_mcp_command(self, model: str, command: str, context: dict[str, Any]) -> str:
        """
        Run an MCP command if supported, otherwise raise or fallback to chat-based inference.
        """
        raise NotImplementedError("MCP not supported for this model.")
