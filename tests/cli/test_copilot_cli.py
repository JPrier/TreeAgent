"""Tests for GitHub Copilot CLI."""

import pytest
from unittest.mock import patch, MagicMock
import sys
from io import StringIO

from src.cli.copilot_cli import parse_copilot_args, create_agent_task, follow_task, list_tasks


def test_parse_copilot_args_create():
    """Test parsing create command arguments."""
    sys.argv = ['gh-copilot-agent-task', 'create', 'Test task', '--follow', '--repo', 'owner/repo']
    args = parse_copilot_args()
    
    assert args.command == 'create'
    assert args.prompt == 'Test task'
    assert args.follow is True
    assert args.repo == 'owner/repo'
    assert args.model_type == 'github_copilot'


def test_parse_copilot_args_follow():
    """Test parsing follow command arguments."""
    sys.argv = ['gh-copilot-agent-task', 'follow', '123', '--repo', 'owner/repo']
    args = parse_copilot_args()
    
    assert args.command == 'follow'
    assert args.task_id == '123'
    assert args.repo == 'owner/repo'


def test_parse_copilot_args_list():
    """Test parsing list command arguments."""
    sys.argv = ['gh-copilot-agent-task', 'list', '--repo', 'owner/repo', '--state', 'closed', '--limit', '5']
    args = parse_copilot_args()
    
    assert args.command == 'list'
    assert args.repo == 'owner/repo'
    assert args.state == 'closed'
    assert args.limit == 5


@patch('src.cli.copilot_cli.create_issue')
@patch('src.cli.copilot_cli.AgentOrchestrator')
def test_create_agent_task_with_repo(mock_orchestrator, mock_create_issue):
    """Test create_agent_task with repository."""
    # Mock GitHub issue creation
    mock_create_issue.return_value = {"url": "https://github.com/owner/repo/issues/123"}
    
    # Mock orchestrator
    mock_project = MagicMock()
    mock_project.completedTasks = []
    mock_project.inProgressTasks = []
    mock_project.failedTasks = []
    mock_project.queuedTasks = []
    mock_project.latestResponse = None
    
    mock_orchestrator_instance = MagicMock()
    mock_orchestrator_instance.implement_project.return_value = mock_project
    mock_orchestrator.return_value = mock_orchestrator_instance
    
    # Capture stdout
    captured_output = StringIO()
    with patch('sys.stdout', captured_output):
        create_agent_task("Test task", "github_copilot", "owner/repo")
    
    # Verify calls
    mock_create_issue.assert_called_once()
    mock_orchestrator_instance.implement_project.assert_called_once()
    
    output = captured_output.getvalue()
    assert "Creating agent task: Test task" in output
    assert "Created GitHub issue:" in output


@patch('src.cli.copilot_cli.get_issue')
def test_follow_task(mock_get_issue):
    """Test follow_task function."""
    mock_get_issue.return_value = {
        "title": "Test Issue",
        "state": "open",
        "author": {"login": "testuser"},
        "body": "Test description",
        "labels": [{"name": "enhancement"}]
    }
    
    captured_output = StringIO()
    with patch('sys.stdout', captured_output):
        follow_task("123", "owner/repo")
    
    mock_get_issue.assert_called_once_with("owner/repo", 123)
    
    output = captured_output.getvalue()
    assert "Task 123: Test Issue" in output
    assert "State: open" in output
    assert "Author: testuser" in output


@patch('src.cli.copilot_cli.list_issues')
def test_list_tasks(mock_list_issues):
    """Test list_tasks function."""
    mock_list_issues.return_value = [
        {"number": 1, "title": "Issue 1", "state": "open", "labels": []},
        {"number": 2, "title": "Issue 2", "state": "closed", "labels": [{"name": "bug"}]}
    ]
    
    captured_output = StringIO()
    with patch('sys.stdout', captured_output):
        list_tasks("owner/repo", "all", 10)
    
    mock_list_issues.assert_called_once_with("owner/repo", "all", 10)
    
    output = captured_output.getvalue()
    assert "Tasks in owner/repo" in output
    assert "#1: Issue 1 (open)" in output
    assert "#2: Issue 2 (closed) [bug]" in output


def test_follow_task_no_repo():
    """Test follow_task without repo raises error."""
    captured_output = StringIO()
    with patch('sys.stdout', captured_output), patch('sys.stderr', captured_output):
        with pytest.raises(SystemExit):
            follow_task("123")
    
    output = captured_output.getvalue()
    assert "Error: --repo is required for following tasks" in output


def test_list_tasks_no_repo():
    """Test list_tasks without repo raises error."""
    captured_output = StringIO()
    with patch('sys.stdout', captured_output), patch('sys.stderr', captured_output):
        with pytest.raises(SystemExit):
            list_tasks()
    
    output = captured_output.getvalue()
    assert "Error: --repo is required for listing tasks" in output