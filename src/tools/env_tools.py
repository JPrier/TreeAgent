import subprocess

from src.modelAccessors.data.tool import Tool


class EnvManager:
    """Run environment commands inside a specific path."""

    def __init__(self, env_path: str) -> None:
        self.env_path = env_path

    def _run(self, cmd: list[str]) -> bool:
        try:
            subprocess.run(
                cmd,
                cwd=self.env_path,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def install_python_requirements(self) -> bool:
        """Install Python dependencies from ``requirements.txt`` using pip."""
        return self._run(["pip", "install", "-r", "requirements.txt"])

    def npm_install(self) -> bool:
        """Install JavaScript dependencies using ``npm install``."""
        return self._run(["npm", "install"])


PYTHON_REQUIREMENTS_TOOL = Tool(
    name="install_python_requirements",
    description="Install Python dependencies from requirements.txt",
    parameters={},
)

NPM_INSTALL_TOOL = Tool(
    name="npm_install",
    description="Install npm dependencies",
    parameters={},
)

