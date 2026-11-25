import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

from tests import fixtures

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "new_adr.py"
TABLE = "# ADRs\n\n| ADR | Decision | Status |\n|---|---|---|\n"


def run(root, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        capture_output=True, text=True, encoding="utf-8",
    )


class NewAdrTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def test_numbers_after_the_base(self):
        repo = fixtures.Repo(self.tmp)
        repo.write("docs/adr/0001-a.md", "# 1. A\n")
        repo.write("docs/adr/README.md", TABLE + "| [0001](0001-a.md) | A | Accepted |\n")
        repo.commit("one")
        repo.branch("work")
        repo.checkout("main")
        repo.write("docs/adr/0002-b.md", "# 2. B\n")
        repo.commit("two")
        repo.checkout("work")
        proc = run(repo.root, "--base", "main", "--title", "Pick a queue")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "docs/adr/0003-pick-a-queue.md")
        self.assertTrue((repo.root / "docs/adr/0003-pick-a-queue.md").is_file())
        index = (repo.root / "docs/adr/README.md").read_text(encoding="utf-8")
        self.assertIn("| [0003](0003-pick-a-queue.md) | Pick a queue | Proposed |", index)
        self.assertEqual(proc.stderr, "")

    def test_three_digit_numbers(self):
        repo = fixtures.Repo(self.tmp)
        repo.write("docs/adr/001-a.md", "# 1. A\n")
        repo.write("docs/adr/002-b.md", "# 2. B\n")
        repo.write("docs/adr/README.md", "- [001](001-a.md) A\n- [002](002-b.md) B\n")
        repo.commit("adrs")
        proc = run(repo.root, "--base", "main", "--title", "C thing")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "docs/adr/003-c-thing.md")
        index = (repo.root / "docs/adr/README.md").read_text(encoding="utf-8")
        self.assertIn("- [003](003-c-thing.md) C thing", index)
        text = (repo.root / "docs/adr/003-c-thing.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# 003. C thing"))

    def test_uses_project_template(self):
        repo = fixtures.Repo(self.tmp)
        repo.write("docs/adr/0000-template.md", "# Title\n\nStatus: Accepted\nDate: YYYY-MM-DD\n\n## Why\n")
        repo.write("docs/adr/0001-a.md", "# 0001. A\n")
        repo.write("docs/adr/README.md", TABLE + "| [0001](0001-a.md) | A | Accepted |\n")
        repo.commit("adrs")
        proc = run(repo.root, "--base", "main", "--title", "Next")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        text = (repo.root / "docs/adr/0002-next.md").read_text(encoding="utf-8")
        self.assertIn("## Why", text)
        self.assertIn(date.today().isoformat(), text)
        self.assertIn("Proposed", text)
        self.assertTrue(text.startswith("# 0002. Next"))

    def test_default_template_sections(self):
        repo = fixtures.Repo(self.tmp)
        repo.write("README.md", "x\n")
        repo.commit("init")
        proc = run(repo.root, "--base", "main", "--title", "Full one")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        text = (repo.root / proc.stdout.strip()).read_text(encoding="utf-8")
        for heading in ("## Context", "## Decision", "## Alternatives considered", "## Consequences"):
            self.assertIn(heading, text)
        self.assertTrue(text.startswith("# 0001. Full one"))

    def test_short_template(self):
        repo = fixtures.Repo(self.tmp)
        repo.write("README.md", "x\n")
        repo.commit("init")
        proc = run(repo.root, "--base", "main", "--short", "--title", "Small one")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        text = (repo.root / proc.stdout.strip()).read_text(encoding="utf-8")
        self.assertNotIn("## Context", text)
        self.assertIn("Proposed", text)
        self.assertIn(date.today().isoformat(), text)

    def test_creates_missing_index(self):
        repo = fixtures.Repo(self.tmp)
        repo.write("README.md", "x\n")
        repo.commit("init")
        proc = run(repo.root, "--base", "main", "--title", "First")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        index = (repo.root / "docs/adr/README.md").read_text(encoding="utf-8")
        self.assertIn("| ADR | Decision | Status |", index)
        self.assertIn("| [0001](0001-first.md) | First | Proposed |", index)
        self.assertNotIn("\r", index)

    def test_refuses_unknown_index(self):
        repo = fixtures.Repo(self.tmp)
        repo.write("docs/adr/README.md", "# Decisions\n\nWe talk about them.\n")
        repo.commit("init")
        proc = run(repo.root, "--base", "main", "--title", "First")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("docs/adr/README.md", proc.stderr)
        self.assertEqual([p.name for p in (repo.root / "docs/adr").iterdir()], ["README.md"])

    def test_without_git_warns(self):
        proc = run(self.tmp, "--title", "No git here")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("warning: base", proc.stderr)
        self.assertEqual(proc.stdout.strip(), "docs/adr/0001-no-git-here.md")
        self.assertEqual(len(proc.stdout.strip().splitlines()), 1)

    def test_refuses_unrecognised_names(self):
        (self.tmp / "docs/adr").mkdir(parents=True)
        (self.tmp / "docs/adr/ADR-0001-x.md").write_text("# x\n", encoding="utf-8")
        proc = run(self.tmp, "--title", "Another")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("ADR-0001-x.md", proc.stderr)
        self.assertEqual([p.name for p in (self.tmp / "docs/adr").iterdir()], ["ADR-0001-x.md"])

    def test_empty_title_is_a_usage_error(self):
        proc = run(self.tmp, "--title", "  ")
        self.assertEqual(proc.returncode, 2)
        self.assertFalse((self.tmp / "docs").exists())

    def test_policy_adr_dir(self):
        policy = "# Docs\n\n```abdullah-docs\nadr-dir: .agents/adr\n```\n"
        (self.tmp / "docs").mkdir()
        (self.tmp / "docs/DOCUMENTATION.md").write_text(policy, encoding="utf-8")
        proc = run(self.tmp, "--policy", "docs/DOCUMENTATION.md", "--title", "Policy dir")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), ".agents/adr/0001-policy-dir.md")
        self.assertTrue((self.tmp / ".agents/adr/0001-policy-dir.md").is_file())

    def test_missing_policy_is_a_usage_error(self):
        proc = run(self.tmp, "--policy", "nope.md", "--title", "X")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("nope.md", proc.stderr)

    def test_crlf_index_keeps_line_endings(self):
        repo = fixtures.Repo(self.tmp)
        repo.write("docs/adr/0001-a.md", "# 1. A\n")
        repo.write("docs/adr/README.md", "# ADRs\n\n- [0001](0001-a.md) A\n", newline="\r\n")
        repo.commit("adrs")
        proc = run(repo.root, "--base", "main", "--title", "B")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        raw = (repo.root / "docs/adr/README.md").read_bytes()
        self.assertIn(b"- [0002](0002-b.md) B\r\n", raw)
        self.assertNotIn(b"\n", raw.replace(b"\r\n", b""))


if __name__ == "__main__":
    unittest.main()
