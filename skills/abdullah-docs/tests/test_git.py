import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import docs_git
from tests import fixtures


class GitTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def test_changed_files_includes_committed_uncommitted_and_untracked(self):
        repo = fixtures.Repo(self.tmp)
        repo.write("keep.md", "keep\n")
        repo.write("edit.md", "one\n")
        repo.commit("initial")
        repo.branch("work")
        repo.write("docs/committed.md", "new\n")
        repo.commit("add committed")
        repo.write("edit.md", "one\ntwo\n")
        repo.write("untracked.md", "u\n")
        changed = docs_git.changed_files(repo.root, "main")
        self.assertEqual(changed, {"docs/committed.md", "edit.md", "untracked.md"})
        self.assertNotIn("keep.md", changed)

    def test_added_lines_reports_new_line_numbers(self):
        repo = fixtures.Repo(self.tmp)
        repo.write("a.md", "1\n2\n3\n")
        repo.commit("initial")
        repo.branch("work")
        repo.write("a.md", "1\n2\n3\n4\n5\n")
        self.assertEqual(docs_git.added_lines(repo.root, "main", "a.md"), {4, 5})

    def test_added_lines_ignores_line_endings(self):
        repo = fixtures.Repo(self.tmp)
        repo.write("a.md", "1\n2\n3\n")
        repo.commit("initial")
        repo.branch("work")
        repo.write("a.md", "1\n2\n3\n", newline="\r\n")
        self.assertEqual(docs_git.added_lines(repo.root, "main", "a.md"), set())

    def test_files_at_reads_the_base(self):
        repo = fixtures.Repo(self.tmp)
        repo.write("README.md", "x\n")
        repo.commit("initial")
        repo.branch("work")
        repo.checkout("main")
        repo.write("docs/adr/0001-first.md", "adr\n")
        repo.commit("add adr on main")
        repo.checkout("work")
        self.assertEqual(docs_git.files_at(repo.root, "main", "docs/adr"), ["0001-first.md"])
        self.assertFalse((repo.root / "docs" / "adr" / "0001-first.md").exists())

    def test_not_a_repository(self):
        (self.tmp / "sub").mkdir()
        (self.tmp / "a.md").write_text("a\n", encoding="utf-8")
        (self.tmp / "sub" / "b.md").write_text("b\n", encoding="utf-8")
        (self.tmp / "node_modules").mkdir()
        (self.tmp / "node_modules" / "c.md").write_text("c\n", encoding="utf-8")
        self.assertFalse(docs_git.is_repo(self.tmp))
        self.assertIsNone(docs_git.git(self.tmp, "rev-parse", "HEAD"))
        self.assertEqual(docs_git.tracked_files(self.tmp, "*.md"), ["a.md", "sub/b.md"])
        self.assertEqual(docs_git.changed_files(self.tmp, "main"), set())

    def test_missing_ref(self):
        repo = fixtures.Repo(self.tmp)
        repo.write("a.md", "a\n")
        repo.commit("initial")
        self.assertFalse(docs_git.ref_exists(repo.root, "origin/main"))
        self.assertIsNone(docs_git.merge_base(repo.root, "origin/main"))
        self.assertIsNone(docs_git.default_base(repo.root))

    def test_changed_files_without_base_uses_head(self):
        repo = fixtures.Repo(self.tmp)
        repo.write("a.md", "a\n")
        repo.commit("initial")
        repo.write("a.md", "a\nb\n")
        repo.write("new.md", "n\n")
        self.assertEqual(docs_git.changed_files(repo.root, None), {"a.md", "new.md"})
        self.assertEqual(docs_git.changed_files(repo.root, "origin/main"), {"a.md", "new.md"})

    def test_commits_since_and_tracked_files(self):
        repo = fixtures.Repo(self.tmp)
        repo.write("a.md", "a\n")
        repo.commit("initial")
        repo.branch("work")
        repo.write("b.md", "b\n")
        repo.commit("feat: add b\n\nRefs: x")
        self.assertEqual(docs_git.commits_since(repo.root, "main"), ["feat: add b\n\nRefs: x"])
        self.assertEqual(docs_git.tracked_files(repo.root, "*.md"), ["a.md", "b.md"])

    def test_merge_reports_conflict_without_raising(self):
        repo = fixtures.Repo(self.tmp)
        repo.write("a.md", "base\n")
        repo.commit("initial")
        repo.branch("work")
        repo.write("a.md", "work\n")
        repo.commit("work edit")
        repo.checkout("main")
        repo.write("a.md", "main\n")
        repo.commit("main edit")
        self.assertFalse(repo.merge("work"))


if __name__ == "__main__":
    unittest.main()
