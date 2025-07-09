from __future__ import annotations

import threading

from modelAccessors.data.tool import Tool


class FileManager:
    """Simple file reader/writer with a shared lock."""

    _lock = threading.Lock()

    def read_file(self, path: str, size: int | None = None) -> str:
        """Return the file contents, optionally limited to ``size`` bytes."""
        with FileManager._lock, open(path, "r", encoding="utf-8") as f:
            return f.read(size) if size is not None else f.read()

    def write_file(self, path: str, content: str) -> bool:
        """Write ``content`` to ``path``. Return ``True`` on success."""
        try:
            with FileManager._lock, open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except OSError:
            return False


_FILE_MANAGER = FileManager()


def read_file(path: str, size: int | None = None) -> str:
    return _FILE_MANAGER.read_file(path, size)


def write_file(path: str, content: str) -> bool:
    return _FILE_MANAGER.write_file(path, content)


READ_FILE_TOOL = Tool(
    name="read_file",
    description="Read a file and return its contents (optionally limited)",
    parameters={"path": {"type": "string"}, "size": {"type": "integer", "optional": True}},
)

WRITE_FILE_TOOL = Tool(
    name="write_file",
    description="Write text content to a file",
    parameters={"path": {"type": "string"}, "content": {"type": "string"}},
)
