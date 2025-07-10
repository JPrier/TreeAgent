import builtins
import io
import os

import tools.file_io as file_io
from tools.file_io import FileManager


def test_read_file_returns_contents(monkeypatch):
    def fake_open(path, mode="r", encoding=None):
        assert path == "/tmp/foo.txt"
        assert mode == "r"
        return io.StringIO("hello")

    monkeypatch.setattr(builtins, "open", fake_open)
    assert file_io.read_file("/tmp/foo.txt") == "hello"


def test_read_file_respects_size_limit(monkeypatch):
    def fake_open(path, mode="r", encoding=None):
        return io.StringIO("hello")

    monkeypatch.setattr(builtins, "open", fake_open)
    assert file_io.read_file("/tmp/foo.txt", size=2) == "he"


def test_write_file_writes_data(monkeypatch):
    written = {}

    class _File(io.StringIO):
        def __exit__(self, exc_type, exc_val, exc_tb):
            written["data"] = self.getvalue()
            return False

    def fake_open(path, mode="w", encoding=None):
        assert path == "/tmp/out.txt"
        assert mode == "w"
        return _File()

    monkeypatch.setattr(builtins, "open", fake_open)
    assert file_io.write_file("/tmp/out.txt", "data") is True
    assert written["data"] == "data"


def test_write_file_handles_error(monkeypatch):
    def fake_open(path, mode="w", encoding=None):
        raise OSError

    monkeypatch.setattr(builtins, "open", fake_open)
    assert file_io.write_file("/bad", "x") is False


def test_lock_is_per_path(monkeypatch):
    paths = []

    class FakeCtx:
        def __init__(self, path):
            self.path = path
        def __enter__(self):
            paths.append(self.path)
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    monkeypatch.setattr(file_io._PathLocks, "lock", lambda p: FakeCtx(p))

    def fake_open(path, mode="r", encoding=None):
        return io.StringIO("x")

    monkeypatch.setattr(builtins, "open", fake_open)

    file_io.read_file("/tmp/a")
    file_io.write_file("/tmp/b", "x")
    assert paths == ["/tmp/a", "/tmp/b"]


def test_read_directory_lists(monkeypatch):
    monkeypatch.setattr(os, "listdir", lambda p: ["a", "b"])

    class FakeCtx:
        def __enter__(self):
            pass
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    monkeypatch.setattr(file_io._PathLocks, "lock", lambda p: FakeCtx())
    assert file_io.read_directory("/dir") == ["a", "b"]


def test_write_directory_rename(monkeypatch):
    called = {}

    class FakeCtx:
        def __enter__(self):
            pass
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    monkeypatch.setattr(file_io._PathLocks, "lock", lambda p: FakeCtx())
    monkeypatch.setattr(os, "rename", lambda a, b: called.setdefault("rename", (a, b)))
    assert file_io.write_directory("/dir", new_name="/new") is True
    assert called["rename"] == ("/dir", "/new")


def test_write_directory_delete(monkeypatch):
    called = {}

    class FakeCtx:
        def __enter__(self):
            pass
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    monkeypatch.setattr(file_io._PathLocks, "lock", lambda p: FakeCtx())
    monkeypatch.setattr(os, "rmdir", lambda p: called.setdefault("delete", p))
    assert file_io.write_directory("/dir", delete=True) is True
    assert called["delete"] == "/dir"

