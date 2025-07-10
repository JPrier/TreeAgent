import builtins
import io
import os
import threading
import time
from contextlib import contextmanager

import tools.file_io as file_io


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

    orig_lock = file_io._PathLocks.lock

    @contextmanager
    def tracking_lock(path):
        paths.append(os.path.abspath(path))
        with orig_lock(path):
            yield

    monkeypatch.setattr(file_io._PathLocks, "lock", tracking_lock)

    def fake_open(path, mode="r", encoding=None):
        return io.StringIO("x")

    monkeypatch.setattr(builtins, "open", fake_open)

    file_io.read_file("/tmp/a")
    file_io.write_file("/tmp/b", "x")
    expected = [os.path.abspath("/tmp/a"), os.path.abspath("/tmp/b")]
    assert paths == expected


def test_read_directory_lists(monkeypatch):
    monkeypatch.setattr(os, "listdir", lambda p: ["a", "b"])
    assert file_io.read_directory("/dir") == ["a", "b"]


def test_write_directory_rename(monkeypatch):
    called = {}
    monkeypatch.setattr(os, "rename", lambda a, b: called.setdefault("rename", (a, b)))
    assert file_io.write_directory("/dir", new_name="/new") is True
    assert called["rename"] == ("/dir", "/new")


def test_write_directory_delete(monkeypatch):
    called = {}
    monkeypatch.setattr(os, "rmdir", lambda p: called.setdefault("delete", p))
    assert file_io.write_directory("/dir", delete=True) is True
    assert called["delete"] == "/dir"



def test_lock_blocks_subpath(tmp_path):
    parent = tmp_path / "parent"
    parent.mkdir()
    child = parent / "child.txt"
    child.touch()
    acquired = []

    def worker():
        with file_io._PathLocks.lock(child):
            acquired.append("child")

    t = threading.Thread(target=worker)
    with file_io._PathLocks.lock(parent):
        t.start()
        time.sleep(0.05)
        assert not acquired
    t.join()
    assert acquired == ["child"]


def test_lock_blocks_parent(tmp_path):
    parent = tmp_path / "parent"
    parent.mkdir()
    child = parent / "child.txt"
    child.touch()
    acquired = []

    def worker():
        with file_io._PathLocks.lock(parent):
            acquired.append("parent")

    t = threading.Thread(target=worker)
    with file_io._PathLocks.lock(child):
        t.start()
        time.sleep(0.05)
        assert not acquired
    t.join()
    assert acquired == ["parent"]


def test_locks_allow_unrelated_paths(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.touch()
    b.touch()
    order = []
    started = threading.Event()

    def hold_a():
        with file_io._PathLocks.lock(a):
            order.append("a")
            started.set()
            time.sleep(0.05)

    def hold_b():
        started.wait()
        with file_io._PathLocks.lock(b):
            order.append("b")

    t1 = threading.Thread(target=hold_a)
    t2 = threading.Thread(target=hold_b)
    start = time.monotonic()
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    assert set(order) == {"a", "b"}
    assert time.monotonic() - start < 0.1
