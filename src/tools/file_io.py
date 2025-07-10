from __future__ import annotations

import os
import threading
from contextlib import contextmanager

from modelAccessors.data.tool import Tool


class _PathLocks:
    """Manage locks for individual paths with hierarchical exclusion."""

    _registry_lock = threading.Lock()
    _locks: dict[str, threading.Lock] = {}
    _active: set[str] = set()

    @classmethod
    @contextmanager
    def lock(cls, path: str):
        abs_path = os.path.abspath(path)
        while True:
            with cls._registry_lock:
                if not any(
                    abs_path == p
                    or abs_path.startswith(p + os.sep)
                    or p.startswith(abs_path + os.sep)
                    for p in cls._active
                ):
                    lock = cls._locks.setdefault(abs_path, threading.Lock())
                    cls._active.add(abs_path)
                    break
            # Simple wait loop for conflicting locks
            threading.Event().wait(0.01)

        lock.acquire()
        try:
            yield
        finally:
            lock.release()
            with cls._registry_lock:
                cls._active.remove(abs_path)


class FileManager:
    """Read and write files or directories with path-level locking."""

    def read_file(self, path: str, size: int | None = None) -> str:
        """Return the file contents, optionally limited to ``size`` bytes."""
        with _PathLocks.lock(path), open(path, "r", encoding="utf-8") as f:
            return f.read(size) if size is not None else f.read()

    def write_file(self, path: str, content: str) -> bool:
        """Write ``content`` to ``path``. Return ``True`` on success."""
        try:
            with _PathLocks.lock(path), open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except OSError:
            return False

    def read_directory(self, path: str, size: int | None = None) -> list[str]:
        """Return the directory contents as a list of names."""
        try:
            with _PathLocks.lock(path):
                items = sorted(os.listdir(path))
        except OSError:
            items = []
        if size is not None:
            items = items[:size]
        return items

    def write_directory(
        self, path: str, *, new_name: str | None = None, delete: bool = False
    ) -> bool:
        """Rename or delete a directory."""
        try:
            with _PathLocks.lock(path):
                if delete:
                    os.rmdir(path)
                    return True
                if new_name:
                    os.rename(path, new_name)
                    return True
        except OSError:
            return False
        return False


_FILE_MANAGER = FileManager()


def read_file(path: str, size: int | None = None) -> str:
    return _FILE_MANAGER.read_file(path, size)


def write_file(path: str, content: str) -> bool:
    return _FILE_MANAGER.write_file(path, content)


def read_directory(path: str, size: int | None = None) -> list[str]:
    return _FILE_MANAGER.read_directory(path, size)


def write_directory(path: str, new_name: str | None = None, delete: bool = False) -> bool:
    return _FILE_MANAGER.write_directory(path, new_name=new_name, delete=delete)


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

READ_DIRECTORY_TOOL = Tool(
    name="read_directory",
    description="List the contents of a directory",
    parameters={"path": {"type": "string"}, "size": {"type": "integer", "optional": True}},
)

WRITE_DIRECTORY_TOOL = Tool(
    name="write_directory",
    description="Rename or delete a directory",
    parameters={
        "path": {"type": "string"},
        "new_name": {"type": "string", "optional": True},
        "delete": {"type": "boolean", "optional": True},
    },
)
