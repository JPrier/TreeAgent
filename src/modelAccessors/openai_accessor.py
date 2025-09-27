import json
from os import environ
from typing import Any, Optional

from openai import OpenAI
from pydantic import TypeAdapter

from .base_accessor import BaseModelAccessor, Tool
from src.dataModel.model_response import ModelResponse

class OpenAIAccessor(BaseModelAccessor):
    def __init__(self):
        self.client = OpenAI(api_key=environ.get("OPENAI_API_KEY"))
        # Models that support structured outputs (json_schema response format)
        # Based on https://platform.openai.com/docs/guides/structured-outputs
        self.supported_models = [
            "gpt-4o", 
            "gpt-4o-mini", 
            "gpt-4o-2024-05-13", 
            "gpt-4o-2024-08-06",
            "gpt-4o-2024-11-20", 
            "gpt-4o-mini-2024-07-18",
            "gpt-5-mini",
            "gpt-5-nano"
        ]
        # Models that support function calling/tools (subset of supported models)
        self.tool_supported_models = ["gpt-4o", "gpt-4o-mini", "gpt-5-mini", "gpt-5-nano"]

    def call_model(
        self,
        prompt: str,
        *,
        adapter: TypeAdapter[ModelResponse],
        schema: dict,
        model: str = "gpt-5-nano",
        system_prompt: str = "",
        tools: Optional[list[Tool]] = None,
    ) -> ModelResponse:
        # Validate that the model is supported
        if model not in self.supported_models:
            supported_models_str = ", ".join(self.supported_models)
            raise ValueError(
                f"Unsupported model '{model}'. OpenAI accessor only supports models with structured outputs: {supported_models_str}"
            )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        
        # Ensure the schema is compatible with OpenAI's requirements
        openai_schema, is_wrapped = self._ensure_openai_compatible_schema(schema)
        
        kwargs = {
            "model": model,
            "messages": messages,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": openai_schema, "strict": True},
            },
        }
        
        if tools and self.supports_tools(model):
            kwargs["tools"] = self._convert_to_openai_tools(tools)
            
        response = self.client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        
        # Use parsed response when available
        parsed = getattr(message, "parsed", None)
        if parsed is not None:
            # If we wrapped the schema, unwrap the response
            if is_wrapped and isinstance(parsed, dict) and "response" in parsed:
                parsed = parsed["response"]
            return adapter.validate_python(parsed)
            
        # Fallback to JSON parsing if parsed is not available
        raw = message.content
        if not raw:
            raise ValueError("No content in response")
        
        # If we wrapped the schema, parse JSON and unwrap the response
        if is_wrapped:
            import json
            parsed_json = json.loads(raw)
            if isinstance(parsed_json, dict) and "response" in parsed_json:
                raw = json.dumps(parsed_json["response"])
        
        return adapter.validate_json(raw)
    
    def supports_tools(self, model: str) -> bool:
        """Check if model supports native tools/function calling"""
        return model in self.tool_supported_models
    
    def _ensure_openai_compatible_schema(self, schema: dict) -> tuple[dict, bool]:
        """
        Ensure the schema is compatible with OpenAI's structured output requirements.
        
        OpenAI requires the root schema to have 'type': 'object', but Pydantic's
        discriminated unions generate schemas with oneOf at the root level.
        
        Returns:
            tuple: (modified_schema, was_wrapped)
        """
        # Check if the schema already has a root type of "object"
        if schema.get("type") == "object":
            return schema, False
        
        # If it's a oneOf/anyOf schema (discriminated union), wrap it in an object
        if "oneOf" in schema or "anyOf" in schema:
            wrapped_schema = {
                "type": "object",
                "properties": {
                    "response": schema
                },
                "required": ["response"],
                "additionalProperties": False
            }
            return wrapped_schema, True
        
        return schema, False
        
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
