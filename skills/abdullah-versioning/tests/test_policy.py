import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import ver_policy  # noqa: E402

FENCE = "```"
DESIGN_BLOCK = f"""# Releasing

{FENCE}abdullah-versioning
layout: dev-staging-main
production: main
staging: staging
integration: dev
sources: Directory.Build.props, src/web/package.json, src/web/package-lock.json
tag: v{{version}}
changelog: CHANGELOG.md
dev-suffix: dev
pre-releases: rc
release-branch: release/{{version}}
hotfix-branch: hotfix/{{version}}-{{name}}
support-branch: support/{{major}}.{{minor}}.x
{FENCE}
"""


def _block(*lines: str) -> str:
    return "\n".join([f"{FENCE}abdullah-versioning", *lines, FENCE, ""])


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, rel: str, text: str) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_defaults_without_policy(self):
        s = ver_policy.read_settings(None)
        self.assertIsNone(s.layout)
        self.assertEqual((s.production, s.staging, s.integration), ("main", "staging", "dev"))
        self.assertEqual(s.sources, [])
        self.assertEqual(s.tag, "v{version}")
        self.assertEqual(s.changelog, "CHANGELOG.md")
        self.assertEqual(s.dev_suffix, "dev")
        self.assertEqual(s.pre_releases, ["rc"])
        self.assertEqual(s.release_branch, "release/{version}")
        self.assertEqual(s.hotfix_branch, "hotfix/{version}-{name}")
        self.assertEqual(s.support_branch, "support/{major}.{minor}.x")

    def test_reads_the_design_example(self):
        s = ver_policy.read_settings(self._write("docs/RELEASING.md", DESIGN_BLOCK))
        self.assertEqual(s.layout, "dev-staging-main")
        self.assertEqual(s.sources, ["Directory.Build.props", "src/web/package.json", "src/web/package-lock.json"])
        self.assertEqual(s.pre_releases, ["rc"])
        self.assertEqual(s.support_branch, "support/{major}.{minor}.x")

    def test_main_layout_turns_dev_suffix_off(self):
        s = ver_policy.read_settings(self._write("a.md", _block("layout: main")))
        self.assertIsNone(s.dev_suffix)
        s = ver_policy.read_settings(self._write("b.md", _block("layout: main", "dev-suffix: dev")))
        self.assertEqual(s.dev_suffix, "dev")
        s = ver_policy.read_settings(self._write("c.md", _block("layout: dev-main", "dev-suffix: none",
                                                                "pre-releases: none")))
        self.assertIsNone(s.dev_suffix)
        self.assertEqual(s.pre_releases, [])

    def test_find_policy_order(self):
        self._write("CONTRIBUTING.md", "# Contributing\n\n" + _block("layout: main"))
        self._write("docs/RELEASING.md", DESIGN_BLOCK)
        self.assertEqual(ver_policy.find_policy(self.root), self.root / "docs/RELEASING.md")
        (self.root / "docs/RELEASING.md").unlink()
        self.assertEqual(ver_policy.find_policy(self.root), self.root / "CONTRIBUTING.md")
        self._write("CONTRIBUTING.md", "# Contributing\n\nNo block here.\n")
        self.assertIsNone(ver_policy.find_policy(self.root))

    def test_first_version(self):
        self.assertEqual(ver_policy.read_settings(None).first_version, "0.1.0")
        s = ver_policy.read_settings(self._write("a.md", _block("layout: main", "first-version: 1.0.0")))
        self.assertEqual(s.first_version, "1.0.0")

    def test_changelog_must_stay_inside_the_repository(self):
        for value in ("../outside.md", "/etc/CHANGELOG.md", "C:/x/CHANGELOG.md"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    ver_policy.read_settings(self._write("a.md", _block("layout: main", f"changelog: {value}")))

    def test_bad_layout(self):
        with self.assertRaises(ValueError) as cm:
            ver_policy.read_settings(self._write("a.md", _block("layout: gitflow")))
        self.assertIn("dev-staging-main", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
