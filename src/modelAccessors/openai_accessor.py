from os import environ
from typing import Any, Optional, Dict
from openai import OpenAI
from pydantic import BaseModel, TypeAdapter
from .base_accessor import BaseModelAccessor, Tool
from src.dataModel.model_response import ModelResponse

class OpenAIAccessor(BaseModelAccessor):
    def __init__(self):
        self.client = OpenAI(api_key=environ.get("OPENAI_API_KEY"))
        # Models that support function calling/tools
        self.tool_supported_models = ["gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-3.5-turbo-0125", "gpt-3.5-turbo"]

    def prompt_model(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        schema: type[BaseModel],
    ) -> ModelResponse:
        """
        Sends a prompt to the specified OpenAI model and returns the validated response.
        """
        openai_schema: Dict[str, Any] = {
            "type": "json_schema",
            "json_schema": {
                "name": schema.__name__,
                "schema": schema.model_json_schema(),
            },
        }

        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            # Pydantic schema enforces model-validated responses via OpenAI's JSON schema mode
            response_format=openai_schema,
        )

        content: str | None = response.choices[0].message.content
        if not content:
            raise ValueError("No content in response")

        return TypeAdapter(schema).validate_json(content)

    def call_model(self, prompt: str, schema: type[BaseModel]) -> ModelResponse:  # pragma: no cover - thin wrapper
        """Convenience wrapper used by simple agent nodes."""
        return self.prompt_model("gpt-4", "", prompt, schema)

    def execute_task_with_tools(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        schema: type[BaseModel],
        tools: Optional[list[Tool]] = None,
    ) -> ModelResponse:
        """
        Execute task with tools - using native function calling if supported
        """
        if not tools or not self.supports_tools(model):
            return self.prompt_model(model, system_prompt, user_prompt, schema)

        # Use native OpenAI function calling
        openai_tools = self._convert_to_openai_tools(tools)

        openai_schema: Dict[str, Any] = {
            "type": "json_schema",
            "json_schema": {
                "name": schema.__name__,
                "schema": schema.model_json_schema(),
            },
        }

        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            tools=openai_tools,
            response_format=openai_schema,
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("No content in response")

        return TypeAdapter(schema).validate_json(content)
    
    def supports_tools(self, model: str) -> bool:
        """Check if model supports native tools/function calling"""
        return model in self.tool_supported_models
        
    def _convert_to_openai_tools(self, tools: list[Tool]) -> list[dict[str, Any]]:
        """Convert our Tool objects to OpenAI's tool format"""
        openai_tools: list[dict[str, Any]] = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": tool.parameters,
                        "required": []  # Could be enhanced with required params
                    }
                }
            })
        return openai_tools
