from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from src.dataModel.project import Project


def save_project_state(project: Project, directory: str | Path) -> Path:
    """Save ``project`` to ``directory`` with a timestamped filename."""
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    file_path = dir_path / f"{timestamp}.json"
    tmp = file_path.with_suffix(file_path.suffix + ".tmp")
    tmp.write_text(json.dumps(project.model_dump(), indent=2))
    tmp.replace(file_path)
    return file_path


def load_project_state(file_path: str | Path) -> Project:
    """Load a :class:`Project` from ``file_path``."""
    data = json.loads(Path(file_path).read_text())
    project = Project.model_validate(data)
    if project.inProgressTasks:
        # tasks might have been mid-flight when the snapshot was taken; restart them
        project.queuedTasks = project.inProgressTasks + project.queuedTasks
        project.inProgressTasks = []
    return project


def latest_snapshot_path(directory: str | Path) -> Path:
    """Return the most recent snapshot file in ``directory``."""
    dir_path = Path(directory)
    snapshots = sorted(dir_path.glob("*.json"))
    if not snapshots:
        raise FileNotFoundError(f"no snapshot in {directory}")
    return snapshots[-1]
