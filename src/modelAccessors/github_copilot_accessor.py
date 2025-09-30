import json
import subprocess
from typing import Any, Optional
import os

from pydantic import TypeAdapter

from .base_accessor import BaseModelAccessor, Tool
from src.dataModel.model_response import ModelResponse


class GitHubCopilotAccessor(BaseModelAccessor):
    """GitHub Copilot accessor that creates agentic tasks and returns issue IDs."""
    
    def __init__(self):
        # Verify that gh CLI is available
        try:
            subprocess.run(['gh', '--version'], capture_output=True, text=True, check=True)
            self._gh_available = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self._gh_available = False
            
        # GitHub Copilot models that support tool usage
        self.tool_supported_models = ["gpt-4", "gpt-3.5-turbo", "gpt-4o"]
    
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
        """
        Call GitHub Copilot to create an agentic task.
        
        This uses the gh copilot CLI to create a GitHub issue with an agentic task
        that will handle the code generation. The response contains the issue ID
        that was created.
        """
        
        if not self._gh_available:
            raise RuntimeError(
                "GitHub CLI (gh) is not available. Please install it and authenticate with 'gh auth login'. "
                "See https://github.com/cli/cli#installation for installation instructions."
            )
        
        # Combine system prompt and user prompt for the task description
        full_prompt = f"{system_prompt}\n\n{prompt}".strip()
        
        try:
            # Create a GitHub Copilot agentic task
            # The command format: gh copilot agent-task create "<description>" [--follow]
            cmd = ['gh', 'copilot', 'agent-task', 'create', full_prompt]
            
            # Add --follow flag to track the task progress
            cmd.append('--follow')
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                env=os.environ.copy()
            )
            
            output = result.stdout.strip()
            
            # Parse the output to extract the issue ID
            # The gh copilot agent-task create command should return an issue URL or ID
            issue_id = self._extract_issue_id(output)
            
            # Create a response with the issue ID
            response_data = {
                "type": "implemented",
                "content": f"GitHub Copilot agentic task created. Issue ID: {issue_id}",
                "artifacts": [issue_id]
            }
            
            return adapter.validate_python(response_data)
            
        except subprocess.CalledProcessError as e:
            # If the command fails, it might be because the extension or feature is not available
            raise RuntimeError(
                f"GitHub Copilot agent-task creation failed: {e.stderr}\n"
                "Make sure you have the GitHub Copilot CLI extension installed: "
                "gh extension install github/gh-copilot"
            ) from e
    
    def _extract_issue_id(self, output: str) -> str:
        """
        Extract the issue ID from gh copilot output.
        
        The output might contain a URL like https://github.com/owner/repo/issues/123
        or just the issue number.
        """
        import re
        
        # Try to find issue URL pattern
        url_match = re.search(r'github\.com/[^/]+/[^/]+/issues/(\d+)', output)
        if url_match:
            return url_match.group(1)
        
        # Try to find standalone issue number
        num_match = re.search(r'#(\d+)', output)
        if num_match:
            return num_match.group(1)
        
        # If no pattern matches, return the full output
        return output
    
    def supports_tools(self, model: str) -> bool:
        """Check if model supports tools."""
        return model in self.tool_supported_models