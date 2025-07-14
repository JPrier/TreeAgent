from .base_accessor import BaseModelAccessor, Tool
from typing import Optional
from ..dataModel.model_response import (
    ModelResponse,
    DecomposedResponse,
    ImplementedResponse,
)
from ..dataModel.task import Task, TaskType

class MockAccessor(BaseModelAccessor):
    """Mock accessor for testing without API calls"""
    
    def __init__(self):
        # Mock models that "support" tools
        self.tool_supported_models = ["mock-gpt-4", "mock-claude"]
    
    def prompt_model(self, model: str, system_prompt: str, user_prompt: str) -> ModelResponse:
        # Return a mock decomposition for DECOMPOSE tasks
        if "decompose" in user_prompt.lower() or "complex" in user_prompt.lower():
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
                ],
            )
        else:
            return ImplementedResponse(content="Mock implementation completed")
    
    def execute_task_with_tools(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[list[Tool]] = None,
    ) -> ModelResponse:
        if tools and self.supports_tools(model):
            # Simulate using tools
            tool_names = [tool.name for tool in tools]
            return ImplementedResponse(
                content=f"Mock task completed using tools: {', '.join(tool_names)}"
            )
        else:
            return ImplementedResponse(content="Mock task with tools completed")
    
    def supports_tools(self, model: str) -> bool:
        """Mock tool support for certain models"""
        return model in self.tool_supported_models
