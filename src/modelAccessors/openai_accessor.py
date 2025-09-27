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
        # Models that support structured outputs (json_schema response format)
        # Based on https://platform.openai.com/docs/guides/structured-outputs
        self.structured_output_models = [
            "gpt-4o", 
            "gpt-4o-mini", 
            "gpt-4o-2024-05-13", 
            "gpt-4o-2024-08-06",
            "gpt-4o-2024-11-20", 
            "gpt-4o-mini-2024-07-18"
        ]

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
        }
        
        # Only use structured outputs for models that support it
        if self.supports_structured_outputs(model):
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": schema, "strict": True},
            }
        else:
            # For models without structured output support, request JSON format
            kwargs["response_format"] = {"type": "json_object"}
            # Enhance the system prompt to request JSON format matching the schema
            json_prompt = f"\nPlease respond with valid JSON that matches this schema: {schema}"
            messages[0]["content"] = (system_prompt + json_prompt).strip()
            
        if tools and self.supports_tools(model):
            kwargs["tools"] = self._convert_to_openai_tools(tools)
            
        response = self.client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        
        # For structured output models, use parsed response if available
        parsed = getattr(message, "parsed", None)
        if parsed is not None:
            return adapter.validate_python(parsed)
            
        # Fallback to JSON parsing for all models
        raw = message.content
        if not raw:
            raise ValueError("No content in response")
        return adapter.validate_json(raw)
    
    def supports_tools(self, model: str) -> bool:
        """Check if model supports native tools/function calling"""
        return model in self.tool_supported_models
    
    def supports_structured_outputs(self, model: str) -> bool:
        """Check if model supports structured outputs (json_schema response format)"""
        return model in self.structured_output_models
        
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
