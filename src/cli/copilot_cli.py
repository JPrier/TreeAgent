"""GitHub Copilot style CLI interface for TreeAgent."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from ..orchestrator import AgentOrchestrator
from ..dataModel.model import AccessorType
from ..tools.github_tools import create_issue, get_issue, comment_on_issue, list_issues


def parse_copilot_args() -> argparse.Namespace:
    """Parse gh copilot agent-task style arguments."""
    parser = argparse.ArgumentParser(
        prog="gh copilot agent-task",
        description="GitHub Copilot style interface for TreeAgent tasks",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # create subcommand
    create_parser = subparsers.add_parser("create", help="Create a new agent task")
    create_parser.add_argument(
        "prompt",
        help="Description of the task to create",
    )
    create_parser.add_argument(
        "--follow",
        action="store_true",
        help="Follow the task progress",
    )
    create_parser.add_argument(
        "--model-type",
        choices=[t.value for t in AccessorType],
        default="github_copilot",
        help="Model accessor to use for the task",
    )
    create_parser.add_argument(
        "--repo",
        help="GitHub repository to create issue in (format: owner/repo)",
    )
    create_parser.add_argument(
        "--checkpoint-dir",
        default="checkpoints",
        help="Directory to store project checkpoints",
    )
    
    # follow subcommand for existing tasks
    follow_parser = subparsers.add_parser("follow", help="Follow an existing task")
    follow_parser.add_argument(
        "task_id",
        help="Task/Issue ID to follow",
    )
    follow_parser.add_argument(
        "--repo",
        help="GitHub repository (format: owner/repo)",
    )
    
    # list subcommand
    list_parser = subparsers.add_parser("list", help="List agent tasks")
    list_parser.add_argument(
        "--repo",
        help="GitHub repository to list issues from (format: owner/repo)",
    )
    list_parser.add_argument(
        "--state",
        choices=["open", "closed", "all"],
        default="open",
        help="Filter by issue state",
    )
    list_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of tasks to list",
    )
    
    return parser.parse_args()


def create_agent_task(prompt: str, model_type: str, repo: Optional[str] = None, 
                     checkpoint_dir: str = "checkpoints", follow: bool = False) -> None:
    """Create a new agent task."""
    print(f"Creating agent task: {prompt}")
    
    # Create GitHub issue if repo is provided
    issue_url = None
    issue_number = None
    if repo:
        try:
            result = create_issue(repo, f"Agent Task: {prompt[:50]}...", prompt)
            issue_url = result.get("url")
            # Extract issue number from URL
            if issue_url:
                issue_number = issue_url.split("/")[-1]
            print(f"Created GitHub issue: {issue_url}")
        except Exception as e:
            print(f"Warning: Could not create GitHub issue: {e}")
    
    # Set up orchestrator
    accessor_type = AccessorType(model_type)
    orchestrator = AgentOrchestrator(default_accessor_type=accessor_type)
    
    # Run the task
    try:
        project = orchestrator.implement_project(prompt, checkpoint_dir=checkpoint_dir)
        
        # Update GitHub issue with results
        if repo and issue_number:
            try:
                summary = f"""Task completed!

**Project Summary:**
- Completed Tasks: {len(project.completedTasks)}
- In Progress Tasks: {len(project.inProgressTasks)}
- Failed Tasks: {len(project.failedTasks)}
- Queued Tasks: {len(project.queuedTasks)}

Latest response type: {project.latestResponse.type if project.latestResponse else "None"}
"""
                comment_on_issue(repo, int(issue_number), summary)
                print(f"Updated GitHub issue with results: {issue_url}")
            except Exception as e:
                print(f"Warning: Could not update GitHub issue: {e}")
        
        # Print summary
        print("\nProject Summary:")
        print(f"Completed Tasks: {len(project.completedTasks)}")
        print(f"In Progress Tasks: {len(project.inProgressTasks)}")
        print(f"Failed Tasks: {len(project.failedTasks)}")
        print(f"Queued Tasks: {len(project.queuedTasks)}")
        
        if follow and repo and issue_number:
            follow_task(issue_number, repo)
            
    except Exception as e:
        print(f"Error executing task: {e}")
        if repo and issue_number:
            try:
                comment_on_issue(repo, int(issue_number), f"Task failed with error: {e}")
            except Exception:
                pass  # Ignore secondary errors
        sys.exit(1)


def follow_task(task_id: str, repo: Optional[str] = None) -> None:
    """Follow an existing task."""
    if not repo:
        print("Error: --repo is required for following tasks")
        sys.exit(1)
    
    try:
        issue = get_issue(repo, int(task_id))
        print(f"Task {task_id}: {issue['title']}")
        print(f"State: {issue['state']}")
        print(f"Author: {issue['author']['login']}")
        if issue.get('labels'):
            labels = [label['name'] for label in issue['labels']]
            print(f"Labels: {', '.join(labels)}")
        print(f"\nDescription:\n{issue['body']}")
    except Exception as e:
        print(f"Error following task {task_id}: {e}")
        sys.exit(1)


def list_tasks(repo: Optional[str] = None, state: str = "open", limit: int = 10) -> None:
    """List agent tasks."""
    if not repo:
        print("Error: --repo is required for listing tasks")
        sys.exit(1)
    
    try:
        issues = list_issues(repo, state, limit)
        print(f"Tasks in {repo} (state: {state}):")
        for issue in issues:
            labels = [label['name'] for label in issue.get('labels', [])]
            label_str = f" [{', '.join(labels)}]" if labels else ""
            print(f"#{issue['number']}: {issue['title']} ({issue['state']}){label_str}")
    except Exception as e:
        print(f"Error listing tasks: {e}")
        sys.exit(1)


def main() -> None:
    """Entry point for the GitHub Copilot style CLI."""
    args = parse_copilot_args()
    
    if not args.command:
        print("Error: No command specified. Use --help for usage information.")
        sys.exit(1)
    
    if args.command == "create":
        create_agent_task(
            args.prompt, 
            args.model_type, 
            args.repo, 
            args.checkpoint_dir, 
            args.follow
        )
    elif args.command == "follow":
        follow_task(args.task_id, args.repo)
    elif args.command == "list":
        list_tasks(args.repo, args.state, args.limit)
    else:
        print(f"Error: Unknown command '{args.command}'")
        sys.exit(1)


if __name__ == "__main__":
    main()