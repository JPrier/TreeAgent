from typing import Optional

from pydantic import TypeAdapter

from .base_accessor import BaseModelAccessor, Tool
from src.dataModel.task import TaskType
from src.dataModel.model_response import ModelResponse

class MockAccessor(BaseModelAccessor):
    """Mock accessor for testing without API calls"""
    
    def __init__(self):
        # Mock models that "support" tools
        self.tool_supported_models = ["mock-gpt-4", "mock-claude"]

    def call_model(
        self,
        prompt: str,
        *,
        adapter: TypeAdapter[ModelResponse],
        schema: dict,
        model: str = "mock-gpt-4",
        system_prompt: str = "",
        tools: Optional[list[Tool]] = None,
    ) -> ModelResponse:  # pragma: no cover - simple wrapper
        data = self._build_response(prompt)
        if data["type"] == "implemented":
            if tools and self.supports_tools(model):
                tool_names = ", ".join(tool.name for tool in tools)
                data["content"] = f"Mock task completed using tools: {tool_names}"
            elif tools:
                data["content"] = "Mock task with tools completed"
        return adapter.validate_python(data)
    
    def supports_tools(self, model: str) -> bool:
        """Mock tool support for certain models"""
        return model in self.tool_supported_models

    def _build_response(self, prompt: str) -> dict:
        if "mock_decompose" in prompt:
            return {
                "type": "decomposed",
                "subtasks": [
                    {
                        "id": "mock-1",
                        "type": TaskType.IMPLEMENT,
                        "description": "Create authentication system",
                    },
                    {
                        "id": "mock-2",
                        "type": TaskType.IMPLEMENT,
                        "description": "Create dashboard interface",
                    },
                ],
            }
        if "mock_follow_up" in prompt:
            return {
                "type": "follow_up_required",
                "content": "Mock follow-up required",
                "follow_up_ask": {
                    "id": "mock-follow-up",
                    "type": TaskType.RESEARCH,
                    "description": "Provide additional details",
                },
            }
        if "mock_fail" in prompt:
            return {
                "type": "failed",
                "error_message": "Mock failure",
                "retryable": False,
            }
        return {"type": "implemented", "content": "Mock implementation completed", "artifacts": []}
