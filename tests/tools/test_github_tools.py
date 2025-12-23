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


@patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'})
def test_github_issue_manager_get_api_headers():
    """Test getting API headers."""
    headers = GitHubIssueManager._get_api_headers()
    assert headers["Authorization"] == "token test_token"
    assert "application/vnd.github.v3+json" in headers["Accept"]


def test_github_issue_manager_no_token():
    """Test that missing token raises an error."""
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(RuntimeError, match="GitHub token not found"):
            GitHubIssueManager._get_api_headers()


@patch('requests.get')
@patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'})
def test_get_issue(mock_get):
    """Test get_issue function."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "number": 123,
        "title": "Test Issue",
        "body": "Test body",
        "state": "open"
    }
    mock_response.content = True
    mock_get.return_value = mock_response
    
    result = get_issue("owner/repo", 123)
    
    assert result["title"] == "Test Issue"
    assert result["state"] == "open"
    mock_get.assert_called_once()
    assert "https://api.github.com/repos/owner/repo/issues/123" in mock_get.call_args[0]


@patch('requests.post')
@patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'})
def test_create_issue(mock_post):
    """Test create_issue function."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "number": 123,
        "html_url": "https://github.com/owner/repo/issues/123"
    }
    mock_response.content = True
    mock_post.return_value = mock_response
    
    result = create_issue("owner/repo", "Test Issue", "Test body", ["bug", "enhancement"])
    
    assert result["number"] == 123
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args[1]
    assert call_kwargs["json"]["title"] == "Test Issue"
    assert call_kwargs["json"]["labels"] == ["bug", "enhancement"]


@patch('requests.patch')
@patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'})
def test_update_issue(mock_patch):
    """Test update_issue function."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"number": 123, "title": "New Title"}
    mock_response.content = True
    mock_patch.return_value = mock_response
    
    result = update_issue("owner/repo", 123, "New Title", "New body")
    
    assert result["title"] == "New Title"
    mock_patch.assert_called_once()
    call_kwargs = mock_patch.call_args[1]
    assert call_kwargs["json"]["title"] == "New Title"
    assert call_kwargs["json"]["body"] == "New body"


@patch('requests.post')
@patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'})
def test_comment_on_issue(mock_post):
    """Test comment_on_issue function."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 456, "body": "Test comment"}
    mock_response.content = True
    mock_post.return_value = mock_response
    
    result = comment_on_issue("owner/repo", 123, "Test comment")
    
    assert result["body"] == "Test comment"
    mock_post.assert_called_once()
    assert "comments" in mock_post.call_args[0][0]


@patch('requests.get')
@patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'})
def test_list_issues(mock_get):
    """Test list_issues function."""
    mock_issues = [
        {"number": 1, "title": "Issue 1", "state": "open"},
        {"number": 2, "title": "Issue 2", "state": "closed"}
    ]
    mock_response = MagicMock()
    mock_response.json.return_value = mock_issues
    mock_response.content = True
    mock_get.return_value = mock_response
    
    result = list_issues("owner/repo", "all", 20)
    
    assert len(result) == 2
    assert result[0]["title"] == "Issue 1"
    mock_get.assert_called_once()
    assert "state=all" in mock_get.call_args[0][0]
    assert "per_page=20" in mock_get.call_args[0][0]


@patch('requests.patch')
@patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'})
def test_close_issue(mock_patch):
    """Test close_issue function."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"number": 123, "state": "closed"}
    mock_response.content = True
    mock_patch.return_value = mock_response
    
    result = close_issue("owner/repo", 123)
    
    assert result["state"] == "closed"
    mock_patch.assert_called_once()
    call_kwargs = mock_patch.call_args[1]
    assert call_kwargs["json"]["state"] == "closed"


def test_tool_definitions():
    """Test that tool definitions are properly structured."""
    assert GET_ISSUE_TOOL.name == "get_github_issue"
    assert "repo" in GET_ISSUE_TOOL.parameters
    assert "issue_number" in GET_ISSUE_TOOL.parameters
    
    assert CREATE_ISSUE_TOOL.name == "create_github_issue"
    assert "repo" in CREATE_ISSUE_TOOL.parameters
    assert "title" in CREATE_ISSUE_TOOL.parameters
    
    assert len(GITHUB_TOOLS) == 6  # All 6 GitHub tools