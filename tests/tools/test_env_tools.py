import subprocess

from tools.env_tools import EnvManager


def test_npm_install_runs_command(monkeypatch):
    calls = {}

    def fake_run(cmd, cwd=None, check=True, stdout=None, stderr=None):
        calls["cmd"] = cmd
        calls["cwd"] = cwd
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    env = EnvManager("/env")
    assert env.npm_install() is True
    assert calls["cmd"] == ["npm", "install"]
    assert calls["cwd"] == "/env"


def test_install_python_requirements_handles_error(monkeypatch):
    def fake_run(cmd, cwd=None, check=True, stdout=None, stderr=None):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(subprocess, "run", fake_run)
    env = EnvManager("/env")
    assert env.install_python_requirements() is False


def test_multiple_envs_independent(monkeypatch):
    cwds = []

    def fake_run(cmd, cwd=None, check=True, stdout=None, stderr=None):
        cwds.append(cwd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    env_a = EnvManager("/a")
    env_b = EnvManager("/b")
    env_a.npm_install()
    env_b.install_python_requirements()
    assert cwds == ["/a", "/b"]

