
from search.file_loader import load_project_files, read_file


def test_load_project_files_filters(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "code.py").write_text("pass")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "readme.txt").write_text("hi")

    # ignored directories
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "mod.py").write_text("ignored")
    (tmp_path / "src" / "__pycache__").mkdir()
    (tmp_path / "src" / "__pycache__" / "cache.py").write_text("ignored")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("ignored")

    # hidden directory
    (tmp_path / "src" / ".hidden").mkdir()
    (tmp_path / "src" / ".hidden" / "secret.py").write_text("ignored")

    # unsupported extension
    (tmp_path / "src" / "note.tmp").write_text("ignore")

    files = load_project_files(tmp_path)
    names = sorted(str(p.relative_to(tmp_path)) for p in files)
    assert names == ["docs/readme.txt", "src/code.py"]


def test_read_file_normalizes_newlines(tmp_path):
    path = tmp_path / "file.py"
    path.write_text("a\r\nb\rc")
    assert read_file(path) == "a\nb\nc"
