"""Command line interface for TreeAgent."""

from __future__ import annotations

import argparse

from .orchestrator import AgentOrchestrator


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run the TreeAgent orchestrator on a project prompt",
    )
    parser.add_argument(
        "prompt",
        help="Description of the project to implement",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for the TreeAgent CLI."""
    args = parse_args()

    orchestrator = AgentOrchestrator()
    project = orchestrator.implement_project(args.prompt)

    print("Project Summary:")
    print(f"Completed Tasks: {len(project.completedTasks)}")
    print(f"In Progress Tasks: {len(project.inProgressTasks)}")
    print(f"Failed Tasks: {len(project.failedTasks)}")
    print(f"Queued Tasks: {len(project.queuedTasks)}")


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()

