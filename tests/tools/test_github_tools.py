"""Tests for GitHub tools."""

import pytest
from unittest.mock import patch, MagicMock
import json

from src.tools.github_tools import (
    get_issue,
    create_issue,
    update_issue,
    comment_on_issue,
    list_issues,
    close_issue,
    GitHubIssueManager,
    GET_ISSUE_TOOL,
    CREATE_ISSUE_TOOL,
    GITHUB_TOOLS,
)


def test_github_issue_manager_run_gh_command_success():
    """Test successful gh command execution."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.stdout = "test output"
        result = GitHubIssueManager._run_gh_command(['issue', 'list'])
        assert result == "test output"
        mock_run.assert_called_once_with(
            ['gh', 'issue', 'list'],
            capture_output=True,
            text=True,
            check=True
        )


def test_github_issue_manager_run_gh_command_no_gh():
    """Test gh command execution when gh CLI is not available."""
    with patch('subprocess.run', side_effect=FileNotFoundError):
        with pytest.raises(RuntimeError, match="GitHub CLI \\(gh\\) is not available"):
            GitHubIssueManager._run_gh_command(['issue', 'list'])


@patch('src.tools.github_tools.GitHubIssueManager._run_gh_command')
def test_get_issue(mock_run_command):
    """Test get_issue function."""
    mock_run_command.return_value = '{"title": "Test Issue", "body": "Test body", "state": "open"}'
    
    result = get_issue("owner/repo", 123)
    
    assert result["title"] == "Test Issue"
    assert result["state"] == "open"
    mock_run_command.assert_called_once_with([
        'issue', 'view', '123', '--repo', 'owner/repo', '--json', 'title,body,state,author,labels,assignees'
    ])


@patch('src.tools.github_tools.GitHubIssueManager._run_gh_command')
def test_create_issue(mock_run_command):
    """Test create_issue function."""
    mock_run_command.return_value = "https://github.com/owner/repo/issues/123"
    
    result = create_issue("owner/repo", "Test Issue", "Test body", ["bug", "enhancement"])
    
    assert result["url"] == "https://github.com/owner/repo/issues/123"
    assert result["created"] is True
    mock_run_command.assert_called_once_with([
        'issue', 'create', '--repo', 'owner/repo', '--title', 'Test Issue', 
        '--body', 'Test body', '--label', 'bug,enhancement'
    ])


@patch('src.tools.github_tools.GitHubIssueManager._run_gh_command')
def test_update_issue(mock_run_command):
    """Test update_issue function."""
    mock_run_command.return_value = ""
    
    result = update_issue("owner/repo", 123, "New Title", "New body")
    
    assert result["updated"] is True
    assert result["issue_number"] == 123
    mock_run_command.assert_called_once_with([
        'issue', 'edit', '123', '--repo', 'owner/repo', '--title', 'New Title', '--body', 'New body'
    ])


@patch('src.tools.github_tools.GitHubIssueManager._run_gh_command')
def test_comment_on_issue(mock_run_command):
    """Test comment_on_issue function."""
    mock_run_command.return_value = ""
    
    result = comment_on_issue("owner/repo", 123, "Test comment")
    
    assert result["commented"] is True
    assert result["issue_number"] == 123
    mock_run_command.assert_called_once_with([
        'issue', 'comment', '123', '--repo', 'owner/repo', '--body', 'Test comment'
    ])


@patch('src.tools.github_tools.GitHubIssueManager._run_gh_command')
def test_list_issues(mock_run_command):
    """Test list_issues function."""
    mock_issues = [
        {"number": 1, "title": "Issue 1", "state": "open"},
        {"number": 2, "title": "Issue 2", "state": "closed"}
    ]
    mock_run_command.return_value = json.dumps(mock_issues)
    
    result = list_issues("owner/repo", "all", 20)
    
    assert len(result) == 2
    assert result[0]["title"] == "Issue 1"
    mock_run_command.assert_called_once_with([
        'issue', 'list', '--repo', 'owner/repo', '--state', 'all', '--limit', '20',
        '--json', 'number,title,state,author,labels'
    ])


@patch('src.tools.github_tools.GitHubIssueManager._run_gh_command')
def test_close_issue(mock_run_command):
    """Test close_issue function."""
    mock_run_command.return_value = ""
    
    result = close_issue("owner/repo", 123, "completed")
    
    assert result["closed"] is True
    assert result["issue_number"] == 123
    mock_run_command.assert_called_once_with([
        'issue', 'close', '123', '--repo', 'owner/repo', '--reason', 'completed'
    ])


def test_tool_definitions():
    """Test that tool definitions are properly structured."""
    assert GET_ISSUE_TOOL.name == "get_github_issue"
    assert "repo" in GET_ISSUE_TOOL.parameters
    assert "issue_number" in GET_ISSUE_TOOL.parameters
    
    assert CREATE_ISSUE_TOOL.name == "create_github_issue"
    assert "repo" in CREATE_ISSUE_TOOL.parameters
    assert "title" in CREATE_ISSUE_TOOL.parameters
    
    assert len(GITHUB_TOOLS) == 6  # All 6 GitHub tools