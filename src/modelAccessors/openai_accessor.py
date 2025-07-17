from os import environ
from typing import Optional
from openai import OpenAI
from pydantic import TypeAdapter
from .base_accessor import BaseModelAccessor, Tool
from dataModel.model_response import ModelResponse

class OpenAIAccessor(BaseModelAccessor):
    def __init__(self):
        self.client = OpenAI(api_key=environ.get("OPENAI_API_KEY"))
        # Models that support function calling/tools
        self.tool_supported_models = ["gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-3.5-turbo-0125", "gpt-3.5-turbo"]

    def prompt_model(self, model: str, system_prompt: str, user_prompt: str) -> ModelResponse:
        """
        Sends a prompt to the specified OpenAI model and returns the response.
        """
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"}
        )
        
        content: str | None = response.choices[0].message.content
        if not content:
            raise ValueError("No content in response")
            
        return TypeAdapter(ModelResponse).validate_json(content) # type: ignore

    def execute_task_with_tools(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[list[Tool]] = None,
    ) -> ModelResponse:
        """
        Execute task with tools - using native function calling if supported
        """
        if not tools or not self.supports_tools(model):
            return self.prompt_model(model, system_prompt, user_prompt)
        
        # Use native OpenAI function calling
        openai_tools = self._convert_to_openai_tools(tools)
        
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            tools=openai_tools,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("No content in response")
            
        return TypeAdapter(ModelResponse).validate_json(content)
    
    def supports_tools(self, model: str) -> bool:
        """Check if model supports native tools/function calling"""
        return model in self.tool_supported_models
        
    def _convert_to_openai_tools(self, tools: list[Tool]) -> list[dict[str, object]]:
        """Convert our Tool objects to OpenAI's tool format"""
        openai_tools: list[dict[str, object]] = []
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
