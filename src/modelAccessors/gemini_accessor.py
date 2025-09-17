from os import environ
import json
from typing import Any, Dict, Optional

import google.generativeai as genai
from pydantic import TypeAdapter

from .base_accessor import BaseModelAccessor, Tool
from src.dataModel.model_response import ModelResponse

class GeminiAccessor(BaseModelAccessor):
    def __init__(self):
        genai.configure(api_key=environ.get("GOOGLE_API_KEY"))
        # Models that support function calling
        self.tool_supported_models = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"]
        
    def call_model(
        self,
        prompt: str,
        *,
        adapter: TypeAdapter[ModelResponse],
        schema: dict,
        model: str = "gemini-1.5-pro",
        system_prompt: str = "",
        tools: Optional[list[Tool]] = None,
    ) -> ModelResponse:
        model_instance = genai.GenerativeModel(model)
        full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

        if tools and self.supports_tools(model):
            gemini_tools = self._convert_to_gemini_tools(tools)
            response = model_instance.generate_content(full_prompt, tools=gemini_tools)
        else:
            response = model_instance.generate_content(full_prompt)

        content = response.text
        if not content:
            raise ValueError("No content in response")

        try:
            json_content = json.loads(content)
        except json.JSONDecodeError:
            json_content = {"text": content}

        return adapter.validate_python(json_content)
    
    def supports_tools(self, model: str) -> bool:
        """Check if model supports function calling"""
        return model in self.tool_supported_models
        
    def _convert_to_gemini_tools(self, tools: list[Tool]) -> list[Dict[str, Any]]:
        """Convert our Tool objects to Gemini's function format"""
        gemini_tools = []
        for tool in tools:
            gemini_tools.append({
                "function_declarations": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": {
                            "type": "object",
                            "properties": tool.parameters
                        }
                    }
                ]
            })
        return gemini_tools
