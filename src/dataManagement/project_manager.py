from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import uuid

from src.dataModel.project import Project


def save_project_state(project: Project, directory: str | Path) -> Path:
    """Save ``project`` to ``directory`` with a timestamped filename.

    Filename pattern (new): YYYYMMDDHHMMSSmmm-<uuid>.json where mmm = milliseconds.
    This guarantees uniqueness even for multiple snapshots within the same second.
    """
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)

    now = datetime.utcnow()
    # 14 digits for seconds + 3 digits for milliseconds
    timestamp = now.strftime("%Y%m%d%H%M%S") + f"{now.microsecond // 1000:03d}"
    unique_id = uuid.uuid4().hex
    file_path = dir_path / f"{timestamp}-{unique_id}.json"
    tmp = file_path.with_suffix(file_path.suffix + ".tmp")
    tmp.write_text(json.dumps(project.model_dump(), indent=2), encoding="utf-8")
    tmp.replace(file_path)
    return file_path


def load_project_state(file_path: str | Path) -> Project:
    """Load a :class:`Project` from ``file_path``."""
    data = json.loads(Path(file_path).read_text(encoding="utf-8"))
    project = Project.model_validate(data)
    if project.inProgressTasks:
        # tasks might have been mid-flight when the snapshot was taken; restart them
        project.queuedTasks = project.inProgressTasks + project.queuedTasks
        project.inProgressTasks = []
    return project


def latest_snapshot_path(directory: str | Path) -> Path:
    """Return the most recent snapshot file in ``directory``.

    Supports both old filenames (YYYYMMDDHHMMSS.json) and new filenames
    (YYYYMMDDHHMMSSmmm-<uuid>.json). Selection is based on the embedded
    timestamp (to millisecond precision when available), with file mtime as a
    secondary tie-breaker.
    """
    dir_path = Path(directory)
    snapshots = list(dir_path.glob("*.json"))
    if not snapshots:
        raise FileNotFoundError(f"no snapshot in {directory}")

    def sort_key(p: Path) -> tuple[float, float]:
        stem = p.stem  # without .json
        ts_part = stem.split("-")[0]
        try:
            if len(ts_part) == 17:  # seconds (14) + ms (3)
                base = datetime.strptime(ts_part[:14], "%Y%m%d%H%M%S")
                ms = int(ts_part[14:17])
                ts = base.timestamp() + ms / 1000.0
            elif len(ts_part) == 14:  # legacy seconds-only
                base = datetime.strptime(ts_part, "%Y%m%d%H%M%S")
                ts = base.timestamp()
            elif len(ts_part) == 20:  # possible future microseconds variant
                base = datetime.strptime(ts_part[:14], "%Y%m%d%H%M%S")
                micros = int(ts_part[14:20])
                ts = base.timestamp() + micros / 1_000_000.0
            else:
                ts = p.stat().st_mtime
        except (ValueError, OSError):
            ts = p.stat().st_mtime
        return (ts, p.stat().st_mtime)

    snapshots.sort(key=sort_key)
    return snapshots[-1]
