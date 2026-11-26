import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import ver_git  # noqa: E402
from ver_semver import Version  # noqa: E402

from .fixtures import Repo  # noqa: E402


class GitTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Repo(Path(self._tmp.name))
        self.repo.write("README.md", "x\n")
        self.repo.commit("init")

    def tearDown(self):
        self._tmp.cleanup()

    def test_tag_versions_skips_other_tags(self):
        for name in ("v0.1.0", "plan1-pre-squash", "v0.3.0-rc.1", "v0.2.0"):
            self.repo.tag(name)
        found = ver_git.tag_versions(self.repo.root, "v{version}")
        self.assertEqual([t for t, _ in found], ["v0.1.0", "v0.2.0", "v0.3.0-rc.1"])
        self.assertEqual(found[1][1], Version.parse("0.2.0"))
        self.assertEqual(ver_git.tag_versions(self.repo.root, "{version}"), [])
        self.assertEqual(sorted(ver_git.all_tags(self.repo.root)),
                         ["plan1-pre-squash", "v0.1.0", "v0.2.0", "v0.3.0-rc.1"])

    def test_prefixed_tag_format(self):
        self.repo.tag("MyLib-1.2.3")
        self.assertEqual([t for t, _ in ver_git.tag_versions(self.repo.root, "MyLib-{version}")], ["MyLib-1.2.3"])

    def test_branches_and_current(self):
        self.repo.branch("dev")
        self.assertEqual(ver_git.branches(self.repo.root), ["dev", "main"])
        self.assertEqual(ver_git.current_branch(self.repo.root), "dev")
        self.repo.detach()
        self.assertIsNone(ver_git.current_branch(self.repo.root))

    def test_branches_containing(self):
        self.repo.tag("v0.1.0")
        self.repo.branch("dev")
        self.assertEqual(ver_git.branches_containing(self.repo.root, "v0.1.0"), ["dev", "main"])

    def test_show(self):
        self.assertEqual(ver_git.show(self.repo.root, "main", "README.md"), "x\n")
        self.assertIsNone(ver_git.show(self.repo.root, "main", "missing.md"))

    def test_not_a_repository(self):
        with tempfile.TemporaryDirectory() as plain:
            root = Path(plain)
            self.assertFalse(ver_git.is_repo(root))
            self.assertIsNone(ver_git.git(root, "status"))
            self.assertIsNone(ver_git.current_branch(root))
            self.assertEqual(ver_git.branches(root), [])
            self.assertEqual(ver_git.tag_versions(root, "v{version}"), [])
            self.assertIsNone(ver_git.remote_url(root))


if __name__ == "__main__":
    unittest.main()
