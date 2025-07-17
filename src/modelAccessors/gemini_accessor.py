from os import environ
import json
from typing import Any, Dict, Optional
from pydantic import TypeAdapter
import google.generativeai as genai
from .base_accessor import BaseModelAccessor, Tool
from dataModel.model_response import ModelResponse

class GeminiAccessor(BaseModelAccessor):
    def __init__(self):
        genai.configure(api_key=environ.get("GOOGLE_API_KEY"))
        # Models that support function calling
        self.tool_supported_models = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"]
        
    def prompt_model(self, model: str, system_prompt: str, user_prompt: str) -> ModelResponse:
        """Basic text prompting for Gemini models"""
        model_instance = genai.GenerativeModel(model)
        
        # Combine system and user prompts
        full_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}"
        
        response = model_instance.generate_content(full_prompt)
        
        content = response.text
        if not content:
            raise ValueError("No content in response")
            
        # Convert content to JSON format if needed
        try:
            json_content = json.loads(content)
        except json.JSONDecodeError:
            # If the model didn't return JSON, wrap it in a simple structure
            json_content = {"text": content}
            
        return TypeAdapter(ModelResponse).validate_python(json_content)
        
    def execute_task_with_tools(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[list[Tool]] = None,
    ) -> ModelResponse:
        """Execute task with tools - native function calling if supported"""
        if not tools or not self.supports_tools(model):
            return self.prompt_model(model, system_prompt, user_prompt)
            
        model_instance = genai.GenerativeModel(model)
        gemini_tools = self._convert_to_gemini_tools(tools)
        
        full_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}"
        
        response = model_instance.generate_content(
            full_prompt,
            tools=gemini_tools
        )
        
        content = response.text
        if not content:
            raise ValueError("No content in response")
            
        # Process and convert to ModelResponse
        try:
            json_content = json.loads(content)
        except json.JSONDecodeError:
            json_content = {"text": content}
            
        return TypeAdapter(ModelResponse).validate_python(json_content)
    
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
