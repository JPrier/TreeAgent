"""Utilities for discovering and reading project files."""

from __future__ import annotations

from pathlib import Path

from . import config


def load_project_files(base_dir: str | Path = ".") -> list[Path]:
    """Recursively collect project files under ``base_dir``.

    Only files whose suffix is listed in :data:`config.ALLOWED_EXTS` are
    included. Paths containing any folder from :data:`config.IGNORED_FOLDERS`
    or hidden directories are skipped.
    """
    base_path = Path(base_dir)
    files: list[Path] = []
    for path in base_path.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in config.ALLOWED_EXTS:
            continue
        if any(part.startswith(".") for part in path.parts):
            continue
        if any(ign in path.parts for ign in config.IGNORED_FOLDERS):
            continue
        files.append(path)
    return files


def read_file(path: str | Path) -> str:
    """Return the UTF-8 contents of ``path`` with normalized newlines."""
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="ignore")
    return text.replace("\r\n", "\n").replace("\r", "\n")
