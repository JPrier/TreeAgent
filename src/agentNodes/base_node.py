from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.dataModel.model_response import ModelResponse


class AgentNode(ABC):
    """Abstract base class for all agent nodes."""

    SCHEMA: Any

    def __call__(self, data: Any, config: dict[str, Any] | None = None) -> dict:
        """Execute the node and return a serialisable dictionary."""
        result = self.execute_task(data)
        return result.model_dump()

    @abstractmethod
    def execute_task(self, data: Any) -> ModelResponse:
        """Perform the node's work and return a ``ModelResponse``."""
        raise NotImplementedError()
