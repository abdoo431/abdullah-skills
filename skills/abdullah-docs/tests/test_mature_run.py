"""Whole-run defects: untracked files with --all and output encoding."""
import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests import fixtures

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import check_docs  # noqa: E402

HEAD = "## Documentation (abdullah-docs)\n"


def _env():
    env = {k: v for k, v in os.environ.items() if k != "PYTHONIOENCODING"}
    env["PYTHONUTF8"] = "0"
    return env


class UntrackedTests(unittest.TestCase):
    def test_all_checks_untracked_documents(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = fixtures.Repo(Path(tmp))
            repo.write("AGENTS.md", HEAD)
            repo.commit("init")
            repo.write("docs/new.md", "[x](missing.md)\n")  # never added
            repo.write(".gitignore", "ignored.md\n")
            repo.write("ignored.md", "[x](missing.md)\n")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = check_docs.main(["--root", tmp, "--base", "main", "--all"])
            lines = [x for x in out.getvalue().splitlines() if ": link:" in x]
            self.assertEqual(code, 1)
            self.assertEqual(lines, ["docs/new.md:1: error: link: link target does not exist: missing.md"])


class EncodingTests(unittest.TestCase):
    def test_check_docs_prints_utf8_when_redirected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = fixtures.Repo(Path(tmp))
            repo.write("AGENTS.md", HEAD)
            repo.write("docs/a.md", "[x](\u0645\u0633\u062a\u0646\u062f.md) `src/a\u2026b.py` `src/\u0645\u0644\u0641.py`\n")
            repo.commit("init")
            proc = subprocess.run(
                [sys.executable, str(SCRIPTS / "check_docs.py"), "--root", tmp, "--base", "main", "--all"],
                capture_output=True, env=_env())
            text = proc.stdout.decode("utf-8")
            self.assertIn("\u0645\u0633\u062a\u0646\u062f.md", text)
            self.assertIn("\u0645\u0644\u0641.py", text)
            self.assertEqual(proc.returncode, 1, proc.stderr)

    def test_every_script_reconfigures_its_streams(self):
        repo_scripts = Path(__file__).resolve().parents[3] / "scripts"
        cases = [(SCRIPTS, "check_docs", []), (SCRIPTS, "new_adr", ["--title", "t"]),
                 (SCRIPTS, "pr_checklist", []), (repo_scripts, "check_frontmatter", [])]
        for folder, module, extra in cases:
            code = (f"import sys; sys.path.insert(0, {str(folder)!r}); import {module}; "
                    f"{module}.main(['--root', 'no-such-folder', *{extra!r}]); "
                    "print(sys.stdout.encoding, sys.stderr.encoding)")
            with tempfile.TemporaryDirectory() as tmp:
                proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                                      env=_env(), cwd=tmp)
            self.assertEqual(proc.stdout.split()[-2:], ["utf-8", "utf-8"], f"{module}: {proc.stdout} {proc.stderr}")


if __name__ == "__main__":
    unittest.main()
