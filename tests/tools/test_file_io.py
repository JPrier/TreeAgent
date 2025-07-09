import builtins
import io

from tools.file_io import FileManager, read_file, write_file


def test_read_file_returns_contents(monkeypatch):
    def fake_open(path, mode="r", encoding=None):
        assert path == "/tmp/foo.txt"
        assert mode == "r"
        return io.StringIO("hello")

    monkeypatch.setattr(builtins, "open", fake_open)
    assert read_file("/tmp/foo.txt") == "hello"


def test_read_file_respects_size_limit(monkeypatch):
    def fake_open(path, mode="r", encoding=None):
        return io.StringIO("hello")

    monkeypatch.setattr(builtins, "open", fake_open)
    assert read_file("/tmp/foo.txt", size=2) == "he"


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
    assert write_file("/tmp/out.txt", "data") is True
    assert written["data"] == "data"


def test_write_file_handles_error(monkeypatch):
    def fake_open(path, mode="w", encoding=None):
        raise OSError

    monkeypatch.setattr(builtins, "open", fake_open)
    assert write_file("/bad", "x") is False


def test_lock_is_used(monkeypatch):
    events = []

    class FakeLock:
        def __enter__(self):
            events.append("enter")

        def __exit__(self, exc_type, exc_val, exc_tb):
            events.append("exit")

    monkeypatch.setattr(FileManager, "_lock", FakeLock())

    def fake_open(path, mode="r", encoding=None):
        return io.StringIO("x")

    monkeypatch.setattr(builtins, "open", fake_open)

    assert read_file("/tmp/x") == "x"
    assert events == ["enter", "exit"]
