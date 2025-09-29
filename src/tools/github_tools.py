import subprocess
import json
from typing import Any, Dict, Optional

from pydantic import BaseModel

from src.modelAccessors.data.tool import Tool


class GitHubIssueManager:
    """Manager for GitHub issue operations using gh CLI."""
    
    @staticmethod
    def _run_gh_command(cmd: list[str]) -> str:
        """Run a gh CLI command and return the output."""
        try:
            result = subprocess.run(
                ['gh'] + cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"GitHub CLI command failed: {e.stderr}") from e
        except FileNotFoundError:
            raise RuntimeError(
                "GitHub CLI (gh) is not available. Please install it and authenticate with 'gh auth login'. "
                "See https://github.com/cli/cli#installation for installation instructions."
            ) from None


def get_issue(repo: str, issue_number: int) -> Dict[str, Any]:
    """Get details of a specific GitHub issue."""
    cmd = ['issue', 'view', str(issue_number), '--repo', repo, '--json', 'title,body,state,author,labels,assignees']
    output = GitHubIssueManager._run_gh_command(cmd)
    return json.loads(output)


def create_issue(repo: str, title: str, body: str = "", labels: Optional[list[str]] = None) -> Dict[str, Any]:
    """Create a new GitHub issue."""
    cmd = ['issue', 'create', '--repo', repo, '--title', title, '--body', body]
    
    if labels:
        cmd.extend(['--label', ','.join(labels)])
    
    output = GitHubIssueManager._run_gh_command(cmd)
    # Extract issue URL/number from output
    issue_url = output.strip()
    return {"url": issue_url, "created": True}


def update_issue(repo: str, issue_number: int, title: Optional[str] = None, body: Optional[str] = None) -> Dict[str, Any]:
    """Update a GitHub issue."""
    cmd = ['issue', 'edit', str(issue_number), '--repo', repo]
    
    if title:
        cmd.extend(['--title', title])
    if body:
        cmd.extend(['--body', body])
    
    GitHubIssueManager._run_gh_command(cmd)
    return {"updated": True, "issue_number": issue_number}


def comment_on_issue(repo: str, issue_number: int, comment: str) -> Dict[str, Any]:
    """Add a comment to a GitHub issue."""
    cmd = ['issue', 'comment', str(issue_number), '--repo', repo, '--body', comment]
    GitHubIssueManager._run_gh_command(cmd)
    return {"commented": True, "issue_number": issue_number}


def list_issues(repo: str, state: str = "open", limit: int = 10) -> list[Dict[str, Any]]:
    """List GitHub issues."""
    cmd = ['issue', 'list', '--repo', repo, '--state', state, '--limit', str(limit), '--json', 'number,title,state,author,labels']
    output = GitHubIssueManager._run_gh_command(cmd)
    return json.loads(output)


def close_issue(repo: str, issue_number: int, reason: Optional[str] = None) -> Dict[str, Any]:
    """Close a GitHub issue."""
    cmd = ['issue', 'close', str(issue_number), '--repo', repo]
    if reason:
        cmd.extend(['--reason', reason])
    
    GitHubIssueManager._run_gh_command(cmd)
    return {"closed": True, "issue_number": issue_number}


# Tool definitions for use with model accessors
GET_ISSUE_TOOL = Tool(
    name="get_github_issue",
    description="Get details of a specific GitHub issue by repository and issue number",
    parameters={
        "repo": {"type": "string", "description": "Repository in format 'owner/repo'"},
        "issue_number": {"type": "integer", "description": "Issue number"}
    }
)

CREATE_ISSUE_TOOL = Tool(
    name="create_github_issue",
    description="Create a new GitHub issue",
    parameters={
        "repo": {"type": "string", "description": "Repository in format 'owner/repo'"},
        "title": {"type": "string", "description": "Issue title"},
        "body": {"type": "string", "description": "Issue body/description"},
        "labels": {"type": "array", "items": {"type": "string"}, "description": "Optional labels for the issue"}
    }
)

UPDATE_ISSUE_TOOL = Tool(
    name="update_github_issue",
    description="Update an existing GitHub issue",
    parameters={
        "repo": {"type": "string", "description": "Repository in format 'owner/repo'"},
        "issue_number": {"type": "integer", "description": "Issue number"},
        "title": {"type": "string", "description": "New title (optional)"},
        "body": {"type": "string", "description": "New body/description (optional)"}
    }
)

COMMENT_ISSUE_TOOL = Tool(
    name="comment_github_issue",
    description="Add a comment to a GitHub issue",
    parameters={
        "repo": {"type": "string", "description": "Repository in format 'owner/repo'"},
        "issue_number": {"type": "integer", "description": "Issue number"},
        "comment": {"type": "string", "description": "Comment text"}
    }
)

LIST_ISSUES_TOOL = Tool(
    name="list_github_issues",
    description="List GitHub issues in a repository",
    parameters={
        "repo": {"type": "string", "description": "Repository in format 'owner/repo'"},
        "state": {"type": "string", "enum": ["open", "closed", "all"], "description": "Issue state filter"},
        "limit": {"type": "integer", "description": "Maximum number of issues to return"}
    }
)

CLOSE_ISSUE_TOOL = Tool(
    name="close_github_issue",
    description="Close a GitHub issue",
    parameters={
        "repo": {"type": "string", "description": "Repository in format 'owner/repo'"},
        "issue_number": {"type": "integer", "description": "Issue number"},
        "reason": {"type": "string", "enum": ["completed", "not_planned"], "description": "Reason for closing"}
    }
)

# All GitHub tools for easy import
GITHUB_TOOLS = [
    GET_ISSUE_TOOL,
    CREATE_ISSUE_TOOL,
    UPDATE_ISSUE_TOOL,
    COMMENT_ISSUE_TOOL,
    LIST_ISSUES_TOOL,
    CLOSE_ISSUE_TOOL,
]