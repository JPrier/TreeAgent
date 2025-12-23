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


def test_extract_issue_id_from_url():
    """Test _extract_issue_id with URL format."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        accessor = GitHubCopilotAccessor()
        
        output = "Created issue: https://github.com/owner/repo/issues/123"
        issue_id = accessor._extract_issue_id(output)
        assert issue_id == "123"


def test_extract_issue_id_from_hash():
    """Test _extract_issue_id with # format."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        accessor = GitHubCopilotAccessor()
        
        output = "Issue #456 created"
        issue_id = accessor._extract_issue_id(output)
        assert issue_id == "456"


def test_call_model_no_gh():
    """Test call_model when gh CLI is not available."""
    with patch('subprocess.run', side_effect=FileNotFoundError):
        accessor = GitHubCopilotAccessor()
        
        with pytest.raises(RuntimeError, match="GitHub CLI \\(gh\\) is not available"):
            accessor.call_model("test prompt", adapter=MagicMock(), schema={})


@patch('subprocess.run')
def test_call_model_success(mock_run):
    """Test successful call_model execution."""
    # Setup mock for gh version check and agent-task create
    mock_run.side_effect = [
        MagicMock(returncode=0),  # gh version check
        MagicMock(stdout='Created issue: https://github.com/owner/repo/issues/42', returncode=0)  # gh copilot agent-task
    ]
    
    accessor = GitHubCopilotAccessor()
    
    # Mock TypeAdapter
    mock_adapter = MagicMock()
    mock_response = MagicMock()
    mock_adapter.validate_python.return_value = mock_response
    
    result = accessor.call_model("test prompt", adapter=mock_adapter, schema={})
    
    # Verify the adapter was called with correct data
    call_args = mock_adapter.validate_python.call_args[0][0]
    assert call_args["type"] == "implemented"
    assert "42" in call_args["content"]
    assert "42" in call_args["artifacts"]
    assert result == mock_response


@patch('subprocess.run')
def test_call_model_failure(mock_run):
    """Test call_model when gh copilot command fails."""
    from subprocess import CalledProcessError
    
    # Setup mock for gh version check succeeds, agent-task fails
    mock_run.side_effect = [
        MagicMock(returncode=0),  # gh version check
        CalledProcessError(1, 'gh', stderr='Extension not found')  # gh copilot agent-task fails
    ]
    
    accessor = GitHubCopilotAccessor()
    
    with pytest.raises(RuntimeError, match="GitHub Copilot agent-task creation failed"):
        accessor.call_model("test prompt", adapter=MagicMock(), schema={})