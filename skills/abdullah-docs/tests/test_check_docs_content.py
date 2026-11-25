import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

from tests import fixtures

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import check_docs  # noqa: E402

HEAD = "## Documentation (abdullah-docs)\n"
CHANGELOG = "# Changelog\n\n## [Unreleased]\n\n## [0.4.0]\n\n- old entry\n"
PAIRS = ("--pairs", "specs/*-design.md:specs/*-design.en.md")


def run(root, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = check_docs.main(["--root", str(root), *args])
    return code, out.getvalue().splitlines()


def only(lines, kind):
    return [x for x in lines if f": {kind}:" in x]


class ContentTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = fixtures.Repo(Path(self._tmp.name))
        self.repo.write("AGENTS.md", HEAD)
        self.repo.write("CHANGELOG.md", CHANGELOG)
        self.repo.write("docs/b.md", "# B\n\n## Sub Part\n")
        self.repo.write("src/mod.py", "x = 1\n")
        self.repo.commit("init")
        self.repo.branch("work")

    def check(self, *args):
        return run(self.repo.root, "--base", "main", *args)

    def test_broken_link(self):
        self.repo.write("docs/a.md", "See [x](missing.md).\n")
        code, lines = self.check()
        self.assertEqual(code, 1)
        self.assertEqual(lines, ["docs/a.md:1: error: link: link target does not exist: missing.md"])

    def test_link_relative_to_file(self):
        self.repo.write("docs/a.md", "See [b](b.md) and [dir](../src) and [abs](/nope.md).\n")
        self.assertEqual(self.check(), (0, []))

    def test_unknown_anchor_is_warning(self):
        self.repo.write("docs/a.md", "# A\n\n[ok](b.md#sub-part) [bad](b.md#nope) [self](#a) [bad2](#zzz)\n")
        code, lines = self.check()
        self.assertEqual(code, 0)
        self.assertEqual(len(only(lines, "anchor")), 2)
        self.assertTrue(all("warning" in x for x in lines))

    def test_link_in_fence_ignored(self):
        self.repo.write("docs/a.md", "```\n[x](missing.md)\n```\n")
        self.assertEqual(self.check(), (0, []))

    def test_missing_code_path(self):
        self.repo.write("docs/a.md", "Run `src/gone.py` now.\n")
        code, lines = self.check()
        self.assertEqual(code, 1)
        self.assertIn("docs/a.md:1: error: code-path:", lines[0])

    def test_code_path_found_from_root_or_file_folder(self):
        self.repo.write("docs/a.md", "`src/mod.py` and `sub/c.py`\n")
        self.repo.write("docs/sub/c.py", "")
        self.assertEqual(self.check(), (0, []))

    def test_changelog_line_in_released_section(self):
        self.repo.write("CHANGELOG.md", CHANGELOG + "- misplaced\n")
        code, lines = self.check()
        self.assertEqual(code, 1)
        self.assertEqual(len(lines), 1)
        self.assertIn("CHANGELOG.md:8: error: changelog:", lines[0])

    def test_changelog_entry_moved_by_merge(self):
        self.repo.write("CHANGELOG.md", "# Changelog\n\n## [Unreleased]\n\n- mine\n\n## [0.4.0]\n\n- old entry\n")
        self.repo.commit("entry")
        self.repo.checkout("main")
        self.repo.write("CHANGELOG.md", "# Changelog\n\n## [Unreleased]\n\n## [0.5.0]\n\n## [0.4.0]\n\n- old entry\n")
        self.repo.commit("release")
        self.repo.checkout("work")
        if not self.repo.merge("main"):
            self.repo.write(
                "CHANGELOG.md",
                "# Changelog\n\n## [Unreleased]\n\n## [0.5.0]\n\n- mine\n\n## [0.4.0]\n\n- old entry\n")
        self.repo.commit("merge main")
        text = (self.repo.root / "CHANGELOG.md").read_text().splitlines()
        entry = text.index("- mine") + 1
        code, lines = self.check()
        self.assertEqual(code, 1)
        self.assertTrue(any(x.startswith(f"CHANGELOG.md:{entry}: error: changelog:") for x in lines), lines)

    def test_changelog_line_under_unreleased_passes(self):
        self.repo.write("CHANGELOG.md", CHANGELOG.replace("## [Unreleased]\n", "## [Unreleased]\n\n- new\n"))
        self.assertEqual(self.check(), (0, []))

    def test_examples_skip_code_paths(self):
        self.repo.write("skills/x/reference/a.md", "`src/gone.py`\n")
        self.repo.write("docs/a.md", "`src/gone.py`\n")
        self.repo.write("DOCUMENTATION.md", "```abdullah-docs\nexamples: skills/**\n```\n")
        code, lines = self.check()
        self.assertEqual(code, 1)
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("docs/a.md:1: error: code-path"))

    def test_release_flag_skips_placement(self):
        self.repo.write("CHANGELOG.md", CHANGELOG + "- misplaced\n")
        self.assertEqual(self.check("--release"), (0, []))

    def test_unreleased_heading_variants(self):
        for heading in ("## Unreleased", "## [unreleased]"):
            self.repo.write("CHANGELOG.md", f"# Changelog\n\n{heading}\n")
            self.assertEqual(self.check(), (0, []), heading)
        self.repo.write("CHANGELOG.md", "# Changelog\n\n## [1.0.0]\n")
        code, lines = self.check()
        self.assertEqual(code, 1)
        self.assertEqual(len(only(lines, "changelog")), 1)

    def test_broken_link_in_released_section_is_warning(self):
        self.repo.write("CHANGELOG.md", CHANGELOG + "- see [x](gone.md) and `src/gone.py`\n")
        _, lines = self.check("--release")
        self.assertEqual(len(lines), 2)
        self.assertTrue(all(": warning: " in x for x in lines))

    def test_pair_missing_counterpart(self):
        self.repo.write("specs/x-design.md", "# X\n")
        code, lines = self.check(*PAIRS)
        self.assertEqual(code, 1)
        self.assertEqual(len(lines), 1)
        self.assertIn("specs/x-design.md:1: error: pair:", lines[0])

    def test_pair_changed_alone(self):
        self.repo.write("specs/x-design.md", "# X\n")
        self.repo.write("specs/x-design.en.md", "# X\n")
        self.repo.commit("specs")
        self.repo.branch("edit")
        self.repo.write("specs/x-design.md", "# X2\n")
        code, lines = run(self.repo.root, "--base", "work", *PAIRS)
        self.assertEqual(code, 1)
        self.assertEqual(len(only(lines, "pair")), 1)
        self.repo.write("specs/x-design.en.md", "# X2\n")
        self.assertEqual(run(self.repo.root, "--base", "work", *PAIRS), (0, []))

    def test_default_scope_is_changed_files(self):
        self.repo.checkout("main")
        self.repo.write("docs/old.md", "[x](gone.md)\n")
        self.repo.commit("old")
        self.repo.checkout("work")
        self.repo.merge("main")
        self.assertEqual(self.check(), (0, []))
        code, lines = self.check("--all")
        self.assertEqual(code, 1)
        self.assertIn("docs/old.md:1: error: link:", lines[0])

    def test_history_glob_downgrades(self):
        self.repo.write("docs/plans/p.md", "[x](gone.md)\n")
        code, lines = self.check("--history", "docs/plans/**")
        self.assertEqual(code, 0)
        self.assertIn("docs/plans/p.md:1: warning: link:", lines[0])

    def test_crlf_line_numbers(self):
        self.repo.write("CHANGELOG.md", CHANGELOG + "- misplaced\n", newline="\r\n")
        code, lines = self.check()
        self.assertEqual(code, 1)
        self.assertIn("CHANGELOG.md:8: error: changelog:", lines[0])


if __name__ == "__main__":
    unittest.main()
