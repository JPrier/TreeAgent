from src.modelAccessors.base_accessor import BaseModelAccessor
from os import environ
from typing import Any, Optional, Dict
from openai import OpenAI
from pydantic import TypeAdapter
from src.dataModel.model_response import ModelResponse

class OpenAIAccessor(BaseModelAccessor):
    def __init__(self):
        self.client = OpenAI(api_key=environ.get("OPENAI_API_KEY"))

    def prompt_model(self, model: str, system_prompt: str, user_prompt: str) -> ModelResponse:
        """
        Sends a prompt to the specified OpenAI model and returns the response.

        :param model: The model to use for generating the response.
        :param messages: A list of messages to send to the model.
        :return: The response from the model.
        """
        response: dict[Any, Any] = self.client.chat.completions.create(
            model=model,  # or any that support structured outputs
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={
                "json_schema": TypeAdapter(ModelResponse).json_schema(),
                "strict": True
            }
        )
        return ModelResponse.model_validate_json(response.choices[0].message.content)

    def execute_task_with_tools(self, model: str, system_prompt: str, user_prompt: str, tools: Optional[Dict[str, Any]] = None) -> ModelResponse:
        """
        Execute task with available tools. For OpenAI (non-agentic), we simulate tool usage through chat.

        :param model: The model to use for generating the response.
        :param system_prompt: The system prompt to guide the model.
        :param user_prompt: The user prompt containing the task.
        :param tools: Optional; a dictionary of available tools and their information.
        :return: The response from the model simulating tool usage.
        """
        if tools:
            # Add tool information to the system prompt for chat-based simulation
            tools_description = self._format_tools_for_prompt(tools)
            enhanced_system_prompt = f"{system_prompt}\n\nAvailable tools:\n{tools_description}\n\nYou can reference these tools in your response, but simulate their execution as needed."
        else:
            enhanced_system_prompt = system_prompt
        
        return self.prompt_model(model, enhanced_system_prompt, user_prompt)

    def _format_tools_for_prompt(self, tools: Dict[str, Any]) -> str:
        """Format tools dictionary into a readable description for the prompt."""
        if not tools:
            return "No tools available."
        
        tool_descriptions = []
        for tool_name, tool_info in tools.items():
            description = tool_info.get('description', 'No description available')
            tool_descriptions.append(f"- {tool_name}: {description}")
        
        return "\n".join(tool_descriptions)

    def supports_mcp(self, model: str) -> bool:
        # OpenAI models do not support direct MCP
        return False

    def run_mcp_command(self, model: str, command: str, context: dict[str, Any]) -> str:
        # Fallback: Use chat to infer MCP command
        system_prompt = f"You are an AI agent. Execute the following MCP command as best as possible: {command}\nContext: {context}"
        user_prompt = "Respond with the result of the command."
        response = self.prompt_model(model, system_prompt, user_prompt)
        return str(response)
