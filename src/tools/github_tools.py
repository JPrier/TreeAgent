import json
import os
from typing import Any, Dict, Optional

import requests

from src.modelAccessors.data.tool import Tool


class GitHubIssueManager:
    """Manager for GitHub issue operations using GitHub API."""
    
    @staticmethod
    def _get_api_headers() -> Dict[str, str]:
        """Get headers for GitHub API requests."""
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if not token:
            raise RuntimeError(
                "GitHub token not found. Set GITHUB_TOKEN or GH_TOKEN environment variable. "
                "You can create a token at https://github.com/settings/tokens"
            )
        
        return {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
    
    @staticmethod
    def _make_api_request(method: str, url: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the GitHub API."""
        headers = GitHubIssueManager._get_api_headers()
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == "PATCH":
                response = requests.patch(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"GitHub API request failed: {e}") from e


def get_issue(repo: str, issue_number: int) -> Dict[str, Any]:
    """Get details of a specific GitHub issue."""
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
    return GitHubIssueManager._make_api_request("GET", url)


def create_issue(repo: str, title: str, body: str = "", labels: Optional[list[str]] = None) -> Dict[str, Any]:
    """Create a new GitHub issue."""
    url = f"https://api.github.com/repos/{repo}/issues"
    data = {
        "title": title,
        "body": body
    }
    if labels:
        data["labels"] = labels
    
    return GitHubIssueManager._make_api_request("POST", url, data)


def update_issue(repo: str, issue_number: int, title: Optional[str] = None, body: Optional[str] = None, state: Optional[str] = None) -> Dict[str, Any]:
    """Update a GitHub issue."""
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
    data = {}
    
    if title:
        data["title"] = title
    if body:
        data["body"] = body
    if state:
        data["state"] = state
    
    return GitHubIssueManager._make_api_request("PATCH", url, data)


def comment_on_issue(repo: str, issue_number: int, comment: str) -> Dict[str, Any]:
    """Add a comment to a GitHub issue."""
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    data = {"body": comment}
    return GitHubIssueManager._make_api_request("POST", url, data)


def list_issues(repo: str, state: str = "open", limit: int = 10) -> list[Dict[str, Any]]:
    """List GitHub issues."""
    url = f"https://api.github.com/repos/{repo}/issues?state={state}&per_page={limit}"
    result = GitHubIssueManager._make_api_request("GET", url)
    # GitHub API returns a list directly
    return result if isinstance(result, list) else [result]


def close_issue(repo: str, issue_number: int) -> Dict[str, Any]:
    """Close a GitHub issue."""
    return update_issue(repo, issue_number, state="closed")


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
        "body": {"type": "string", "description": "New body/description (optional)"},
        "state": {"type": "string", "enum": ["open", "closed"], "description": "New state (optional)"}
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
        "issue_number": {"type": "integer", "description": "Issue number"}
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