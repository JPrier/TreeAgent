from .base_accessor import BaseModelAccessor
from typing import Optional, Dict, Any
from ..dataModel.model_response import ModelResponse

class AnthropicAccessor(BaseModelAccessor):
    def prompt_model(self, model: str, system_prompt: str, user_prompt: str) -> ModelResponse:
        # TODO: Implement Anthropic API call here
        raise NotImplementedError("AnthropicAccessor.prompt_model not implemented yet.")
    
    def execute_task_with_tools(self, model: str, system_prompt: str, user_prompt: str, tools: Optional[Dict[str, Any]] = None) -> ModelResponse:
        """
        Execute task with available tools. For future agentic Anthropic models, this could use native tool calling.
        For now, simulate through chat like OpenAI.
        """
        if tools:
            tools_description = self._format_tools_for_prompt(tools)
            enhanced_system_prompt = f"{system_prompt}\n\nAvailable tools:\n{tools_description}\n\nYou can use these tools to complete the task."
        else:
            enhanced_system_prompt = system_prompt
        
        return self.prompt_model(model, enhanced_system_prompt, user_prompt)
    
    def _format_tools_for_prompt(self, tools: Dict[str, Any]) -> str:
        """Format tools dictionary into a readable description for the prompt."""
        if not tools:
            return "No tools available."
        
        tool_descriptions: list[str] = []
        for tool_name, tool_info in tools.items():
            description = tool_info.get('description', 'No description available')
            tool_descriptions.append(f"- {tool_name}: {description}")
        
        return "\n".join(tool_descriptions)
    
    def supports_mcp(self, model: str) -> bool:
        # Future: some Anthropic models might support direct MCP
        return model.startswith("claude-3.5") and "computer-use" in model.lower()  # Example logic
