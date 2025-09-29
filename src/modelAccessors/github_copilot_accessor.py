import json
import subprocess
from typing import Any, Optional

from pydantic import TypeAdapter

from .base_accessor import BaseModelAccessor, Tool
from src.dataModel.model_response import ModelResponse


class GitHubCopilotAccessor(BaseModelAccessor):
    """GitHub Copilot accessor using gh copilot CLI."""
    
    def __init__(self):
        # Verify that gh CLI is available
        try:
            result = subprocess.run(['gh', '--version'], capture_output=True, text=True, check=True)
            self._gh_available = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self._gh_available = False
            
        # GitHub Copilot models that support tool usage
        self.tool_supported_models = ["gpt-4", "gpt-3.5-turbo"]
    
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
        """Call GitHub Copilot using gh copilot CLI."""
        
        if not self._gh_available:
            raise RuntimeError(
                "GitHub CLI (gh) is not available. Please install it and authenticate with 'gh auth login'. "
                "See https://github.com/cli/cli#installation for installation instructions."
            )
        
        # Auto-include GitHub tools if not already provided
        if tools is None:
            from ..tools.github_tools import GITHUB_TOOLS
            tools = GITHUB_TOOLS
        elif tools and not any(tool.name.startswith('github') for tool in tools):
            # Add GitHub tools if they're not already included
            from ..tools.github_tools import GITHUB_TOOLS
            tools = tools + GITHUB_TOOLS
        
        # Combine system prompt and user prompt
        full_prompt = f"{system_prompt}\n\n{prompt}".strip()
        
        if tools and self.supports_tools(model):
            # Format tools into the prompt for now, as gh copilot may not support native tool calling
            tools_description = self._format_tools_for_prompt(tools)
            full_prompt += f"\n\nAvailable tools:\n{tools_description}"
            full_prompt += "\n\nWhen using tools, format your response as JSON with the structure matching the expected schema."
        
        try:
            # Use gh copilot to generate response
            cmd = ['gh', 'copilot', 'suggest', '--type', 'shell']
            
            # For now, we'll use the suggest command and parse the output
            # In a real implementation, you might want to use the API directly
            result = subprocess.run(
                cmd,
                input=full_prompt,
                capture_output=True,
                text=True,
                check=True
            )
            
            content = result.stdout.strip()
            
            # Try to parse as JSON first, fallback to text response
            try:
                json_content = json.loads(content)
            except json.JSONDecodeError:
                # If it's not JSON, wrap it in a basic response structure
                json_content = {
                    "type": "implemented",
                    "content": content,
                    "artifacts": []
                }
            
            return adapter.validate_python(json_content)
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"GitHub Copilot CLI call failed: {e.stderr}") from e
    
    def supports_tools(self, model: str) -> bool:
        """Check if model supports tools (currently limited support)."""
        return model in self.tool_supported_models
    
    def _format_tools_for_prompt(self, tools: list[Tool]) -> str:
        """Format tools into a readable description for the prompt."""
        tool_descriptions = []
        for tool in tools:
            params_desc = ", ".join(f"{k}" for k in tool.parameters.keys())
            tool_descriptions.append(f"- {tool.name}: {tool.description} [Parameters: {params_desc}]")
        
        return "\n".join(tool_descriptions)