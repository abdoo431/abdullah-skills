"""A throwaway git repository for tests, isolated from the user's git configuration."""
import os
import subprocess
from pathlib import Path


class Repo:
    def __init__(self, tmp: Path):
        self.root = Path(tmp)
        # Ignore the user's global and system config (hooks, autocrlf, signing) for every fixture call.
        self._env = dict(
            os.environ,
            GIT_CONFIG_GLOBAL=os.devnull,
            GIT_CONFIG_NOSYSTEM="1",
            GIT_TERMINAL_PROMPT="0",
        )
        self._run("init", "-q", "-b", "main")
        self._run("config", "user.name", "Test User")
        self._run("config", "user.email", "test@example.com")
        self._run("config", "core.autocrlf", "false")
        self._run("config", "commit.gpgsign", "false")

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "--no-pager", *args], cwd=self.root, env=self._env,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            stdin=subprocess.DEVNULL,
        )

    def _must(self, *args: str) -> None:
        proc = self._run(*args)
        if proc.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr}")

    def write(self, path: str, text: str, newline: str = "\n") -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.replace("\n", newline).encode("utf-8"))

    def commit(self, message: str) -> None:
        self._must("add", "-A")
        self._must("commit", "-q", "-m", message)

    def branch(self, name: str) -> None:
        """Create the branch from the current one and switch to it."""
        self._must("checkout", "-q", "-b", name)

    def checkout(self, name: str) -> None:
        self._must("checkout", "-q", name)

    def merge(self, name: str) -> bool:
        """Merge name into the current branch; False on a conflict (left unresolved)."""
        return self._run("merge", "--no-edit", name).returncode == 0
