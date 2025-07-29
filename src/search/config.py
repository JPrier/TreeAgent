"""Configuration for project file discovery."""

from __future__ import annotations

ALLOWED_EXTS: set[str] = {".py", ".md", ".txt", ".json", ".toml"}

IGNORED_FOLDERS: set[str] = {".git", "__pycache__", "node_modules", "dist", "build"}
