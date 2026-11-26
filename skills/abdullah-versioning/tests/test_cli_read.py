import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import version  # noqa: E402

from .fixtures import Repo  # noqa: E402
from .test_survey import changelog, props, released_dev_main  # noqa: E402

POLICY = "# Releasing\n\n```abdullah-versioning\nlayout: dev-main\nsources: Directory.Build.props, src/web/package.json\n```\n"


def run(*argv: str):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = version.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class CliReadTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Repo(Path(self._tmp.name))
        self.root = str(self.repo.root)
        released_dev_main(self.repo)
        self.repo.write("docs/RELEASING.md", POLICY)
        self.repo.commit("policy")

    def tearDown(self):
        self._tmp.cleanup()

    def test_survey_json_shape(self):
        code, out, _ = run("survey", "--root", self.root, "--json")
        self.assertEqual(code, 0)
        data = json.loads(out)
        for key in ("verdict", "current", "layout", "roles", "sources", "stops"):
            self.assertIn(key, data)
        self.assertEqual(data["current"], "0.2.0")

    def test_status_lines(self):
        code, out, _ = run("status", "--root", self.root)
        self.assertEqual(code, 0)
        self.assertIn("branch: dev\n", out)
        self.assertIn("role: integration\n", out)
        self.assertIn("latest: 0.2.0\n", out)
        self.assertIn("agree: yes\n", out)

    def test_plan_output(self):
        self.repo.write("CHANGELOG.md", changelog("0.2.0", "0.1.0", unreleased="### Added\n\n- workspace export"))
        code, out, _ = run("plan", "--root", self.root)
        self.assertEqual(code, 0)
        self.assertIn("next: 0.3.0\n", out)
        self.assertIn("part: minor\n", out)
        self.assertIn("reason: Added: workspace export\n", out)

    def test_plan_with_nothing_to_release(self):
        code, _, err = run("plan", "--root", self.root)
        self.assertEqual(code, 1)
        self.assertIn("[Unreleased] has no entries to release", err)

    def test_notes(self):
        code, out, _ = run("notes", "0.2.0", "--root", self.root)
        self.assertEqual(code, 0)
        self.assertEqual(out, "### Added\n\n- Release 0.2.0.\n")

    def test_check_passes_on_dev(self):
        code, out, _ = run("check", "--root", self.root)
        self.assertEqual((code, out), (0, ""))

    def test_check_role(self):
        self.repo.write("Directory.Build.props", props("0.2.0"))
        self.repo.write("src/web/package.json", '{\n  "name": "web",\n  "version": "0.2.0"\n}\n')
        code, out, _ = run("check", "--root", self.root)
        self.assertEqual(code, 1)
        self.assertEqual(out.count(": error: role:"), 1)

    def test_check_sources_disagree(self):
        self.repo.write("Directory.Build.props", props("0.2.0"))
        code, out, _ = run("check", "--root", self.root)
        self.assertEqual(code, 1)
        self.assertIn(": error: sources:", out)

    def test_check_changelog(self):
        self.repo.write("CHANGELOG.md", changelog("0.2.0", "0.2.0", "0.1.0"))
        code, out, _ = run("check", "--root", self.root)
        self.assertEqual(code, 1)
        self.assertEqual(out.count(": error: changelog:"), 1)

    def test_usage_errors(self):
        self.assertEqual(run("frobnicate", "--root", self.root)[0], 2)
        self.assertEqual(run("notes", "1.2", "--root", self.root)[0], 2)


if __name__ == "__main__":
    unittest.main()
