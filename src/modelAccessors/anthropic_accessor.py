from os import environ
from typing import Any, Optional, Dict
from pydantic import TypeAdapter
from anthropic import Anthropic
from .base_accessor import BaseModelAccessor, Tool
from dataModel.model_response import ModelResponse

class AnthropicAccessor(BaseModelAccessor):
    def __init__(self):
        self.client = Anthropic(api_key=environ.get("ANTHROPIC_API_KEY"))
        # Models with tool support
        self.tool_supported_models = ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-5-sonnet-20240620"]
        
    def prompt_model(self, model: str, system_prompt: str, user_prompt: str) -> ModelResponse:
        """Basic text prompting for Claude models"""
        response = self.client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        content = response.content[0].text
        if not content:
            raise ValueError("No content in response")
            
        return TypeAdapter(ModelResponse).validate_json(content)

    def call_model(self, prompt: str, schema) -> ModelResponse:  # pragma: no cover - thin wrapper
        """Convenience wrapper used by simple agent nodes."""
        return self.prompt_model("claude-3-opus-20240229", "", prompt)
        
    def execute_task_with_tools(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[list[Tool]] = None,
    ) -> ModelResponse:
        """Execute task with tools - native tools if supported"""
        if not tools:
            return self.prompt_model(model, system_prompt, user_prompt)
            
        if self.supports_tools(model):
            # Use Claude's native tool use
            claude_tools = self._convert_to_claude_tools(tools)
            
            response = self.client.messages.create(
                model=model,
                max_tokens=4096,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                tools=claude_tools
            )
            
            content = response.content[0].text
            if not content:
                raise ValueError("No content in response")
                
            return TypeAdapter(ModelResponse).validate_json(content)
        else:
            # Fallback for models without tool support
            tools_description = self._format_tools_for_prompt(tools)
            enhanced_system_prompt = f"{system_prompt}\n\nAvailable tools:\n{tools_description}"
            return self.prompt_model(model, enhanced_system_prompt, user_prompt)
    
    def supports_tools(self, model: str) -> bool:
        """Check if model supports native tool use"""
        return model in self.tool_supported_models
        
    def _convert_to_claude_tools(self, tools: list[Tool]) -> list[Dict[str, Any]]:
        """Convert our Tool objects to Claude's tool format"""
        claude_tools = []
        for tool in tools:
            claude_tools.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": {
                    "type": "object",
                    "properties": tool.parameters,
                    "required": []
                }
            })
        return claude_tools
        
    def _format_tools_for_prompt(self, tools: list[Tool]) -> str:
        """Format tools into a readable description for the prompt"""
        tool_descriptions = []
        for tool in tools:
            params_desc = ", ".join(f"{k}" for k in tool.parameters.keys())
            tool_descriptions.append(f"- {tool.name}: {tool.description} [Parameters: {params_desc}]")
        
        return "\n".join(tool_descriptions)
