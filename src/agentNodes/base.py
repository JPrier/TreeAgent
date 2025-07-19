from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from dataModel.model_response import ModelResponse


class AgentNode(ABC):
    """Common interface for all agent nodes."""

    SCHEMA: type[ModelResponse]

    @abstractmethod
    def execute_task(self, task: Any) -> ModelResponse:
        """Perform the node's work and return a response."""
        raise NotImplementedError

    def __call__(self, task: Any, config: dict[str, Any] | None = None) -> dict:
        """Execute the node and return a serialized response."""
        return self.execute_task(task).model_dump()
