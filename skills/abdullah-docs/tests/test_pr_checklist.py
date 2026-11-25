import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests import fixtures

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "pr_checklist.py"


def run(root, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        capture_output=True, text=True, encoding="utf-8",
    )


class PrChecklistTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = fixtures.Repo(Path(self._tmp.name))
        self.repo.write("README.md", "# x\n")
        self.repo.write("CHANGELOG.md", "# Changelog\n")
        self.repo.write("src/old.py", "x = 1\n")
        self.repo.commit("init")
        self.repo.branch("work")

    def test_full_branch(self):
        self.repo.write("src/app.py", "y = 2\n")
        self.repo.write("tests/test_app.py", "pass\n")
        self.repo.write("docs/runbooks/deploy.md", "# Deploy\n")
        self.repo.write("docs/adr/0001-a.md", "# 1. A\n")
        self.repo.commit("feat: add app\n\nRefs: design 1")
        self.repo.write("src/old.py", "x = 3\n")
        self.repo.commit("fix: tweak old")
        proc = run(self.repo.root, "--base", "main")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.splitlines(), [
            "- spec-or-adr: docs/adr/0001-a.md",
            "- changelog: not changed (2 source files changed)",
            "- public-interface: check by hand (new source files: src/app.py)",
            "- regression-test: tests/test_app.py",
            "- runbook: docs/runbooks/deploy.md",
            "- commit-refs: fix: tweak old",
        ])
        self.assertEqual(proc.stderr, "")

    def test_markdown_only(self):
        self.repo.write("README.md", "# y\n")
        self.repo.commit("docs: edit")
        proc = run(self.repo.root, "--base", "main")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        lines = proc.stdout.splitlines()
        self.assertEqual(lines[0], "- spec-or-adr: none changed")
        self.assertEqual(lines[1], "- changelog: not changed (0 source files changed)")
        self.assertEqual(lines[2], "- public-interface: check by hand")
        self.assertEqual(lines[3], "- regression-test: none changed")
        self.assertEqual(lines[4], "- runbook: none added")
        self.assertEqual(lines[5], "- commit-refs: n/a (no commit uses Refs:)")

    def test_changelog_changed_and_all_refs(self):
        self.repo.write("CHANGELOG.md", "# Changelog\n- x\n")
        self.repo.write("src/old.py", "x = 9\n")
        self.repo.commit("fix: a\n\nRefs: #1")
        lines = run(self.repo.root, "--base", "main").stdout.splitlines()
        self.assertEqual(lines[1], "- changelog: changed (1 source files changed)")
        self.assertEqual(lines[5], "- commit-refs: all commits reference")

    def test_deleted_files_do_not_count(self):
        (self.repo.root / "src/old.py").unlink()
        self.repo.commit("refactor: drop old")
        lines = run(self.repo.root, "--base", "main").stdout.splitlines()
        self.assertEqual(lines[1], "- changelog: not changed (0 source files changed)")

    def test_no_base_warns_and_uses_uncommitted(self):
        self.repo.write("src/new.py", "z = 1\n")
        proc = run(self.repo.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        lines = proc.stdout.splitlines()
        self.assertTrue(lines[0].startswith(".:1: warning: base: "), lines[0])
        self.assertEqual(len(lines), 7)
        self.assertEqual(lines[2], "- changelog: not changed (1 source files changed)")
        self.assertEqual(lines[3], "- public-interface: check by hand (new source files: src/new.py)")
        self.assertEqual(lines[6], "- commit-refs: n/a (no commit uses Refs:)")

    def test_usage_errors(self):
        self.assertEqual(run(self.repo.root / "nope").returncode, 2)
        self.assertEqual(run(self.repo.root, "--policy", "missing.md").returncode, 2)


if __name__ == "__main__":
    unittest.main()
