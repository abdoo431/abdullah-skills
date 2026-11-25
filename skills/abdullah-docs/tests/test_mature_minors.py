"""Case-sensitive globs, GitHub-style heading slugs and a leading BOM."""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

from tests import fixtures

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import check_docs  # noqa: E402
import docs_git  # noqa: E402
import docs_policy  # noqa: E402
import pr_checklist  # noqa: E402
from docs_markdown import heading_slugs  # noqa: E402

HEAD = "## Documentation (abdullah-docs)\n"
BOM = "\ufeff"


def run(root, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = check_docs.main(["--root", str(root), "--base", "main", *args])
    return code, out.getvalue().splitlines()


class GlobCaseTests(unittest.TestCase):
    def test_history_glob_is_case_sensitive(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = fixtures.Repo(Path(tmp))
            repo.write("AGENTS.md", HEAD)
            repo.write("docs/plans/p.md", "[x](gone.md)\n")
            repo.commit("init")
            code, lines = run(tmp, "--all", "--history", "docs/Plans/**")
            self.assertEqual(code, 1)
            self.assertIn("docs/plans/p.md:1: error: link:", lines[0])

    def test_test_file_patterns_are_case_sensitive(self):
        self.assertTrue(pr_checklist._is_test("src/test_a.py"))
        self.assertFalse(pr_checklist._is_test("src/TEST_a.py"))

    def test_walk_pattern_is_case_sensitive(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "a.MD").write_text("x")
            (Path(tmp) / "b.md").write_text("x")
            self.assertEqual(docs_git.tracked_files(Path(tmp), "*.md"), ["b.md"])


class SlugTests(unittest.TestCase):
    def test_link_heading_uses_the_link_text_only(self):
        self.assertEqual(heading_slugs("## [Title](u.md)\n"), {"title"})

    def test_code_and_emphasis_markers_are_dropped(self):
        text = "## `Code` and *em* and _it_ and **bold**\n## snake_case word\n"
        self.assertEqual(heading_slugs(text), {"code-and-em-and-it-and-bold", "snake_case-word"})


class BomTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = fixtures.Repo(Path(self._tmp.name))

    def test_agent_section_on_line_one_after_a_bom(self):
        (self.repo.root / "CLAUDE.md").write_bytes((BOM + HEAD).encode("utf-8"))
        self.repo.commit("init")
        self.assertEqual(run(self.repo.root, "--all"), (0, []))

    def test_policy_block_after_a_bom(self):
        path = self.repo.root / "DOCUMENTATION.md"
        path.write_bytes((BOM + "```abdullah-docs\nadr-dir: records\n```\n").encode("utf-8"))
        self.assertEqual(docs_policy.read_settings(path).adr_dir, "records")


if __name__ == "__main__":
    unittest.main()
