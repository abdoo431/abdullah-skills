import argparse
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import fixtures

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import check_docs  # noqa: E402
import docs_findings  # noqa: E402

ADR = "# {n}. T\n\nStatus: {s}\nDate: 2026-01-01\n"
INDEX = "# ADRs\n\n| ADR | Status |\n|---|---|\n"
HEAD = "## Documentation (abdullah-docs)\n"


def run(root, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = check_docs.main(["--root", str(root), *args])
    return code, out.getvalue().splitlines()


def make_args(root, history=None):
    return argparse.Namespace(root=str(root), base="main", all=False, release=False, adr_dir=None,
                              changelog=None, pairs=None, history=history, policy=None)


class CheckDocsAdrTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = fixtures.Repo(Path(self._tmp.name))
        self.adr("0001-a.md")
        self.adr("0002-b.md")
        self.repo.write("AGENTS.md", HEAD)
        self.index("0001-a.md", "0002-b.md")
        self.repo.commit("init")
        self.repo.branch("work")

    def adr(self, name, status="Accepted", d="docs/adr"):
        self.repo.write(f"{d}/{name}", ADR.format(n=name[:4], s=status))

    def index(self, *names, d="docs/adr"):
        rows = "".join(f"| [{n[:4]}]({n}) | Accepted |\n" for n in names)
        self.repo.write(f"{d}/README.md", INDEX + rows)

    def check(self, *args):
        return run(self.repo.root, "--base", "main", *args)

    def test_clean_repository_exits_zero(self):
        self.assertEqual(self.check(), (0, []))

    def test_missing_index_row(self):
        self.adr("0003-c.md")
        code, lines = self.check()
        self.assertEqual(code, 1)
        self.assertEqual(len(lines), 1)
        self.assertIn("docs/adr/0003-c.md:1: error: adr-index:", lines[0])

    def test_dangling_index_link(self):
        self.index("0001-a.md", "0002-b.md", "0004-d.md")
        code, lines = self.check()
        self.assertEqual(code, 1)
        self.assertTrue(any("error: adr-index" in x and "0004-d.md" in x for x in lines))

    def test_number_taken_on_base(self):
        self.repo.checkout("main")
        self.adr("0003-other.md")
        self.repo.commit("other")
        self.repo.checkout("work")
        self.adr("0003-mine.md")
        self.index("0001-a.md", "0002-b.md", "0003-mine.md")
        code, lines = self.check()
        self.assertEqual(code, 1)
        hit = [x for x in lines if "error: adr-number" in x]
        self.assertEqual(len(hit), 1)
        self.assertIn("0003-mine.md", hit[0])
        self.assertIn("0003-other.md", hit[0])
        self.assertIn("renumber", hit[0])

    def test_local_duplicate_number(self):
        self.adr("0002-c.md")
        self.index("0001-a.md", "0002-b.md", "0002-c.md")
        code, lines = self.check()
        self.assertEqual(code, 1)
        self.assertEqual(len([x for x in lines if "error: adr-number" in x]), 2)

    def test_missing_status_or_date(self):
        self.repo.write("docs/adr/0001-a.md", "# 1. A\n\nDate: 2026-01-01\n")
        self.repo.write("docs/adr/0002-b.md", "# 2. B\n\nStatus: Accepted\n")
        code, lines = self.check()
        self.assertEqual(code, 1)
        self.assertTrue(any("0001-a.md" in x and "adr-header" in x and "status" in x for x in lines))
        self.assertTrue(any("0002-b.md" in x and "adr-header" in x and "date" in x for x in lines))

    def test_superseded_link_must_resolve(self):
        self.adr("0001-a.md", "Superseded by [0002](0002-b.md)")
        self.assertEqual(self.check(), (0, []))
        self.adr("0001-a.md", "Superseded by [0009](0009-z.md)")
        code, lines = self.check()
        self.assertEqual(code, 1)
        self.assertIn("error: adr-header", lines[0])

    def test_superseded_adr_content_findings_are_warnings(self):
        self.adr("0001-a.md", "Superseded by [0009](0009-z.md)")
        ctx, _ = check_docs.build_context(make_args(self.repo.root))
        self.assertEqual(check_docs.severity_for(ctx, "docs/adr/0001-a.md"), "warning")
        self.assertEqual(check_docs.severity_for(ctx, "docs/adr/0002-b.md"), "error")

        def link_check(c):
            path = "docs/adr/0001-a.md"
            return [docs_findings.Finding(path, 5, check_docs.severity_for(c, path), "link", "broken")]

        with mock.patch.object(check_docs, "CHECKS", [link_check, check_docs.check_adr]):
            code, lines = self.check()
        self.assertTrue(any("warning: link" in x for x in lines))
        self.assertTrue(any("error: adr-header" in x for x in lines))
        self.assertEqual(code, 1)

    def test_history_glob(self):
        ctx, _ = check_docs.build_context(make_args(self.repo.root, history=["docs/old/*"]))
        self.assertTrue(check_docs.is_history(ctx, "docs/old/x.md"))
        self.assertFalse(check_docs.is_history(ctx, "docs/new/x.md"))

    def test_unrecognised_adr_name_is_warning(self):
        self.repo.write("docs/adr/ADR-0009-x.md", "# x\n")
        code, lines = self.check()
        self.assertEqual(code, 0)
        self.assertEqual(len(lines), 1)
        self.assertIn("warning: adr-name", lines[0])
        self.assertIn("ADR-0009-x.md", lines[0])

    def test_agent_section_missing_is_warning(self):
        self.repo.write("AGENTS.md", "# Agents\n")
        code, lines = self.check()
        self.assertEqual(code, 0)
        self.assertEqual(len(lines), 1)
        self.assertIn("warning: agent-section", lines[0])

    def test_unfetched_base_warns_once(self):
        self.adr("0003-c.md")
        code, lines = run(self.repo.root, "--base", "origin/main")
        self.assertEqual(code, 1)
        self.assertEqual(len([x for x in lines if "warning: base" in x]), 1)
        self.assertTrue(any("error: adr-index" in x and "0003-c.md" in x for x in lines))

    def test_policy_block_is_read(self):
        self.adr("0001-x.md", d=".agents/adr")
        self.repo.write("docs/DOCUMENTATION.md", "```abdullah-docs\nadr-dir: .agents/adr\n```\n")
        code, lines = self.check("--policy", "docs/DOCUMENTATION.md")
        self.assertEqual(code, 1)
        self.assertTrue(any(".agents/adr/README.md" in x and "adr-index" in x for x in lines))

    def test_missing_policy_is_usage_error(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code, _ = self.check("--policy", "nope.md")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
