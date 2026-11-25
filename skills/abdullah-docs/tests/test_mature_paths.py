"""False positives of the code-path and link checks seen on a large monorepo."""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

from tests import fixtures

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import check_docs  # noqa: E402
from docs_markdown import is_repo_path  # noqa: E402

HEAD = "## Documentation (abdullah-docs)\n"


def run(root, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = check_docs.main(["--root", str(root), "--base", "main", "--all", *args])
    return code, out.getvalue().splitlines()


class MaturePathTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = fixtures.Repo(Path(self._tmp.name))
        self.repo.write("AGENTS.md", HEAD)
        self.repo.write("web/src/api/client.ts", "")
        self.repo.write("src/backend/Acme.Api/Hosting/WebApp.cs", "")
        self.repo.write(".gitignore", "dist/\n")
        self.repo.commit("init")

    def doc(self, text, path="docs/a.md"):
        self.repo.write(path, text)
        self.repo.commit("doc")
        return run(self.repo.root)

    def test_path_relative_to_a_subproject(self):
        text = "`src/api/client.ts` `./src/api/client.ts` `Hosting/WebApp.cs` `web/src/api/client.ts`\n"
        self.assertEqual(self.doc(text), (0, []))

    def test_suffix_match_needs_a_segment_boundary(self):
        code, lines = self.doc("`pi/client.ts` `src/api/other.ts`\n")
        self.assertEqual(code, 1)
        self.assertEqual(len(lines), 2)

    def test_build_outputs_ignored_by_git_are_skipped(self):
        self.assertEqual(self.doc("`dist/index.html` `web/dist/index.html`\n"), (0, []))

    def test_unignored_missing_path_still_reported(self):
        code, lines = self.doc("`build/index.html`\n")
        self.assertEqual(code, 1)
        self.assertIn("code-path", lines[0])

    def test_placeholders_are_not_paths(self):
        text = ("`chore/release-X.Y.Z` `results/run-yyyy-MM-dd-HHmm.json` `results/RUN-YYYY-MM-DD.json` "
                "`docs/NNNN-title.md` `src/a/b…c.py`\n")
        self.assertEqual(self.doc(text), (0, []))

    def test_placeholder_link_targets_are_skipped(self):
        self.assertEqual(self.doc("[NNNN](NNNN-title.md) [x](docs/YYYY-notes.md)\n"), (0, []))

    def test_version_like_names_are_not_paths(self):
        self.assertEqual(self.doc("`chore/release-0.4.0` `v1/2.5`\n"), (0, []))
        self.assertFalse(is_repo_path("chore/release-0.4.0"))
        self.assertTrue(is_repo_path("a/b.7z") is False)
        self.assertTrue(is_repo_path("a/b.py"))

    def test_adr_template_files_are_skipped(self):
        self.repo.write("docs/adr/README.md", "[a](0001-first.md)\n")
        self.repo.write("docs/adr/0001-first.md", "# 1. First\n\n- Status: Accepted\n- Date: 2026-01-01\n")
        self.repo.write("docs/adr/0000-template.md", "[x](nope-0.md) `src/none.py`\n")
        self.repo.write("docs/adr/template.md", "[x](nope-1.md) `src/none.py`\n")
        self.repo.commit("adr")
        self.assertEqual(run(self.repo.root), (0, []))


if __name__ == "__main__":
    unittest.main()
