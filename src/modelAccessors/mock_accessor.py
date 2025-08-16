from .base_accessor import BaseModelAccessor, Tool
from typing import Optional, cast
from pydantic import BaseModel, TypeAdapter
from src.dataModel.model_response import (
    ModelResponse,
    DecomposedResponse,
    ImplementedResponse,
    FollowUpResponse,
    FailedResponse,
)
from src.dataModel.task import Task, TaskType

class MockAccessor(BaseModelAccessor):
    """Mock accessor for testing without API calls"""
    
    def __init__(self):
        # Mock models that "support" tools
        self.tool_supported_models = ["mock-gpt-4", "mock-claude"]

    def call_model(self, prompt: str, schema: type[BaseModel]) -> ModelResponse:  # pragma: no cover - simple wrapper
        """Simpler call method used by node tests."""
        return self.prompt_model("mock-gpt-4", "", prompt, schema)

    def prompt_model(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        schema: type[BaseModel],
    ) -> ModelResponse:
        _ = user_prompt  # prompt content not used for mock responses
        response = self._build_response(schema)
        validated = TypeAdapter(schema).validate_python(response.model_dump())
        return cast(ModelResponse, validated)
    
    def execute_task_with_tools(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        schema: type[BaseModel],
        tools: Optional[list[Tool]] = None,
    ) -> ModelResponse:
        _ = user_prompt  # prompt content not used for mock responses
        response = self._build_response(schema)

        if isinstance(response, ImplementedResponse):
            if tools and self.supports_tools(model):
                # Simulate using tools
                tool_names = [tool.name for tool in tools]
                response.content = (
                    f"Mock task completed using tools: {', '.join(tool_names)}"
                )
            else:
                response.content = "Mock task with tools completed"

        validated = TypeAdapter(schema).validate_python(response.model_dump())
        return cast(ModelResponse, validated)
    
    def supports_tools(self, model: str) -> bool:
        """Mock tool support for certain models"""
        return model in self.tool_supported_models

    def _build_response(self, schema: type[BaseModel]) -> ModelResponse:
        if issubclass(schema, DecomposedResponse):
            return DecomposedResponse(
                subtasks=[
                    Task(
                        id="mock-1",
                        type=TaskType.IMPLEMENT,
                        description="Create authentication system",
                    ),
                    Task(
                        id="mock-2",
                        type=TaskType.IMPLEMENT,
                        description="Create dashboard interface",
                    ),
                ]
            )

        if issubclass(schema, FollowUpResponse):
            return FollowUpResponse(
                content="Mock follow-up required",
                follow_up_ask=Task(
                    id="mock-follow-up",
                    type=TaskType.RESEARCH,
                    description="Provide additional details",
                ),
            )

        if issubclass(schema, FailedResponse):
            return FailedResponse(error_message="Mock failure", retryable=False)

        return ImplementedResponse(content="Mock implementation completed")
