from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from pydantic import TypeAdapter

from src.dataModel.model_response import ModelResponse
from .data.tool import Tool


class BaseModelAccessor(ABC):
    @abstractmethod
    def call_model(
        self,
        prompt: str,
        *,
        adapter: TypeAdapter[ModelResponse],
        schema: dict,
        model: str = "gpt-4",
        system_prompt: str = "",
        tools: Optional[list[Tool]] = None,
    ) -> ModelResponse:
        """Execute a model call with optional tool support."""
        raise NotImplementedError

    def supports_tools(self, model: str) -> bool:
        """Check if a model supports native tool use"""
        return False

