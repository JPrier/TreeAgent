"""Tests for GitHub Copilot accessor."""

import pytest
from unittest.mock import patch, MagicMock
from src.modelAccessors.github_copilot_accessor import GitHubCopilotAccessor


def test_github_copilot_accessor_init():
    """Test GitHubCopilotAccessor initialization."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        accessor = GitHubCopilotAccessor()
        assert accessor._gh_available is True
        assert "gpt-4" in accessor.tool_supported_models


def test_github_copilot_accessor_init_no_gh():
    """Test GitHubCopilotAccessor initialization when gh CLI is not available."""
    with patch('subprocess.run', side_effect=FileNotFoundError):
        accessor = GitHubCopilotAccessor()
        assert accessor._gh_available is False


def test_supports_tools():
    """Test supports_tools method."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        accessor = GitHubCopilotAccessor()
        assert accessor.supports_tools("gpt-4") is True
        assert accessor.supports_tools("unsupported-model") is False


def test_format_tools_for_prompt():
    """Test _format_tools_for_prompt method."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        accessor = GitHubCopilotAccessor()
        
        from src.modelAccessors.data.tool import Tool
        tools = [
            Tool(name="test_tool", description="Test tool", parameters={"param1": {"type": "string"}}),
            Tool(name="another_tool", description="Another tool", parameters={"param2": {"type": "int"}})
        ]
        
        result = accessor._format_tools_for_prompt(tools)
        assert "test_tool: Test tool [Parameters: param1]" in result
        assert "another_tool: Another tool [Parameters: param2]" in result


def test_call_model_no_gh():
    """Test call_model when gh CLI is not available."""
    with patch('subprocess.run', side_effect=FileNotFoundError):
        accessor = GitHubCopilotAccessor()
        
        with pytest.raises(RuntimeError, match="GitHub CLI \\(gh\\) is not available"):
            accessor.call_model("test prompt", adapter=MagicMock(), schema={})


@patch('subprocess.run')
def test_call_model_success(mock_run):
    """Test successful call_model execution."""
    # Setup mock for gh version check
    mock_run.side_effect = [
        MagicMock(returncode=0),  # gh version check
        MagicMock(stdout='{"type": "implemented", "content": "test response", "artifacts": []}')  # gh copilot call
    ]
    
    accessor = GitHubCopilotAccessor()
    
    # Mock TypeAdapter
    mock_adapter = MagicMock()
    mock_adapter.validate_python.return_value = {"type": "implemented", "content": "test response"}
    
    result = accessor.call_model("test prompt", adapter=mock_adapter, schema={})
    
    mock_adapter.validate_python.assert_called_once()
    assert mock_run.call_count == 2  # version check + actual call