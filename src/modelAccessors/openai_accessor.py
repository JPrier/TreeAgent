from os import environ
from typing import Any, Optional

from openai import OpenAI
from pydantic import TypeAdapter

from .base_accessor import BaseModelAccessor, Tool
from src.dataModel.model_response import ModelResponse

class OpenAIAccessor(BaseModelAccessor):
    def __init__(self):
        self.client = OpenAI(api_key=environ.get("OPENAI_API_KEY"))
        # Models that support function calling/tools
        self.tool_supported_models = ["gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-3.5-turbo-0125", "gpt-3.5-turbo"]

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
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        kwargs = {
            "model": model,
            "messages": messages,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": schema, "strict": True},
            },
        }
        if tools and self.supports_tools(model):
            kwargs["tools"] = self._convert_to_openai_tools(tools)
        response = self.client.chat.completions.create(**kwargs)
        raw = response.choices[0].message.content[0].text
        return adapter.validate_json(raw)
    
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
