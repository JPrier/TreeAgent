from .base_accessor import BaseModelAccessor
from typing import Optional, Dict, Any
from ..dataModel.model_response import ModelResponse, DecomposedResponse, ImplementedResponse
from ..dataModel.task import Task, TaskType

class MockAccessor(BaseModelAccessor):
    """Mock accessor for testing without API calls"""
    
    def prompt_model(self, model: str, system_prompt: str, user_prompt: str) -> ModelResponse:
        # Return a mock decomposition for DECOMPOSE tasks
        if "decompose" in user_prompt.lower() or "complex" in user_prompt.lower():
            return DecomposedResponse(
                subtasks=[
                    Task(
                        task_id="mock-1", 
                        task_type=TaskType.IMPLEMENT_CODE,
                        prompt="Create authentication system"
                    ),
                    Task(
                        task_id="mock-2", 
                        task_type=TaskType.IMPLEMENT_CODE,
                        prompt="Create dashboard interface"
                    )
                ]
            )
        else:
            return ImplementedResponse(summary="Mock implementation completed")
    
    def execute_task_with_tools(self, model: str, system_prompt: str, user_prompt: str, tools: Optional[Dict[str, Any]] = None) -> ModelResponse:
        return ImplementedResponse(summary="Mock task with tools completed")
