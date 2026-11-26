import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from .fixtures import Repo  # noqa: E402
from .test_cli_read import run  # noqa: E402

POLICY = "# Releasing\n\n```abdullah-versioning\nlayout: dev-main\nsources: {sources}\n```\n"
CHANGELOG = """# Changelog

## [Unreleased]

{unreleased}

## [0.1.0] - 2026-11-03

### Added

- First release.
"""


def make(root: Path, unreleased: str = "### Added\n\n- Export.", sources: str = "VERSION, app/__init__.py",
         version: str = "0.1.0") -> Repo:
    """main tagged v0.1.0, then dev and release/0.2.0; the files declare `version`."""
    repo = Repo(root)
    repo.write("VERSION", f"{version}\n")
    repo.write("app/__init__.py", f'__version__ = "{version}"\n')
    repo.write("CHANGELOG.md", CHANGELOG.format(unreleased=unreleased))
    repo.write("docs/RELEASING.md", POLICY.format(sources=sources))
    repo.commit("init")
    repo.tag("v0.1.0")
    repo.branch("dev")
    repo.branch("release/0.2.0")
    return repo


def snapshot(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*")
            if p.is_file() and ".git" not in p.relative_to(root).parts}


class CliWriteTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def read(self, rel: str) -> str:
        return (self.root / rel).read_text(encoding="utf-8")

    def test_prepare_final(self):
        make(self.root)
        code, out, err = run("prepare", "0.2.0", "--date", "2026-11-26", "--root", str(self.root))
        self.assertEqual(code, 0, err)
        self.assertIn("## [0.2.0] - 2026-11-26\n\n### Added\n\n- Export.", self.read("CHANGELOG.md"))
        self.assertEqual(self.read("VERSION"), "0.2.0\n")
        self.assertEqual(self.read("app/__init__.py"), '__version__ = "0.2.0"\n')
        self.assertIn("declared: 0.2.0\n", out)

    def test_prepare_pre_release(self):
        make(self.root)
        code, out, err = run("prepare", "0.2.0", "--pre", "rc", "--date", "2026-11-26", "--root", str(self.root))
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read("VERSION"), "0.2.0-rc.1\n")
        self.assertEqual(self.read("app/__init__.py"), '__version__ = "0.2.0rc1"\n')
        self.assertIn("## [0.2.0] - 2026-11-26", self.read("CHANGELOG.md"))

    def test_declare_folds_unreleased_into_open_section(self):
        repo = make(self.root)
        self.assertEqual(run("prepare", "0.2.0", "--pre", "rc", "--date", "2026-11-26", "--root", str(self.root))[0], 0)
        repo.commit("cut")
        repo.tag("v0.2.0-rc.1")
        text = self.read("CHANGELOG.md").replace("## [Unreleased]\n", "## [Unreleased]\n\n### Fixed\n\n- A crash.\n", 1)
        repo.write("CHANGELOG.md", text)
        code, _, err = run("declare", "0.2.0-rc.2", "--root", str(self.root))
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read("VERSION"), "0.2.0-rc.2\n")
        cl = self.read("CHANGELOG.md")
        self.assertIn("## [Unreleased]\n\n## [0.2.0] - 2026-11-26\n\n### Added\n\n- Export.\n\n### Fixed\n\n- A crash.", cl)
        code, _, err = run("declare", "0.2.0", "--date", "2026-12-01", "--root", str(self.root))
        self.assertEqual(code, 0, err)
        self.assertIn("## [0.2.0] - 2026-12-01", self.read("CHANGELOG.md"))
        self.assertEqual(self.read("VERSION"), "0.2.0\n")

    def test_declare_dev_after_release(self):
        repo = make(self.root)
        repo.checkout("dev")
        repo.branch("release/0.2.0-dev")
        before = self.read("CHANGELOG.md")
        code, _, err = run("declare", "0.2.0-dev", "--root", str(self.root))
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read("VERSION"), "0.2.0-dev\n")
        self.assertEqual(self.read("app/__init__.py"), '__version__ = "0.2.0.dev0"\n')
        self.assertEqual(self.read("CHANGELOG.md"), before)

    def _refused(self, setup, *argv: str) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup(root)
            before = snapshot(root)
            code, _, err = run(*argv, "--root", str(root))
            self.assertEqual(code, 1, err)
            self.assertIn("refused", err)
            self.assertEqual(snapshot(root), before)

    def test_refusals(self):
        def disagree(root):
            make(root)
            (root / "app/__init__.py").write_text('__version__ = "0.1.5"\n', encoding="utf-8")

        def rc_tagged(root):
            repo = make(root, version="0.2.0-rc.1")
            repo.tag("v0.2.0-rc.1")

        def on_dev(root):
            make(root).checkout("dev")

        def on_support(root):
            repo = make(root)
            repo.run("checkout", "-q", "-b", "support/0.1.x", "v0.1.0")

        cases = {
            "not greater": (make, "prepare", "0.1.0"),
            "empty unreleased": (lambda r: make(r, unreleased=""), "prepare", "0.2.0"),
            "sources disagree": (disagree, "prepare", "0.2.0"),
            "stage back": (rc_tagged, "declare", "0.2.0-beta.1"),
            "first major": (make, "prepare", "1.0.0"),
            "long-lived branch": (on_dev, "declare", "0.2.0-dev"),
            "outside the support line": (on_support, "declare", "0.2.1"),
            "dev is not a stage": (make, "prepare", "0.2.0", "--pre", "dev"),
        }
        for name, (setup, *argv) in cases.items():
            with self.subTest(name):
                self._refused(setup, *argv)

    def test_hotfix_allowed_during_rc(self):
        repo = make(self.root, unreleased="### Fixed\n\n- A crash.", version="0.2.0")
        repo.checkout("main")
        repo.tag("v0.2.0")
        repo.tag("v0.3.0-rc.1")
        repo.branch("hotfix/0.2.1-crash")
        code, _, err = run("prepare", "0.2.1", "--date", "2026-12-02", "--root", str(self.root))
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read("VERSION"), "0.2.1\n")

    def test_hotfix_on_an_older_line(self):
        repo = make(self.root, unreleased="### Fixed\n\n- A crash.")
        repo.checkout("main")
        repo.write("VERSION", "0.2.0\n")
        repo.write("app/__init__.py", '__version__ = "0.2.0"\n')
        repo.commit("0.2.0")
        repo.tag("v0.2.0")
        repo.run("checkout", "-q", "-b", "support/0.1.x", "v0.1.0")
        repo.branch("hotfix/0.1.1-crash")
        code, _, err = run("prepare", "0.1.1", "--date", "2026-12-02", "--root", str(self.root))
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read("VERSION"), "0.1.1\n")

    def test_carry(self):
        repo = make(self.root)
        repo.run("checkout", "-q", "-b", "support/0.1.x", "v0.1.0")
        repo.write("CHANGELOG.md", self.read("CHANGELOG.md").replace(
            "## [0.1.0]", "## [0.1.1] - 2026-12-01\n\n### Fixed\n\n- A crash.\n\n## [0.1.0]"))
        repo.commit("0.1.1")
        repo.checkout("main")
        repo.write("CHANGELOG.md", self.read("CHANGELOG.md").replace(
            "## [0.1.0]", "## [0.2.0] - 2026-11-26\n\n### Added\n\n- Export.\n\n## [0.1.0]"))
        code, _, err = run("carry", "0.1.1", "--from", "support/0.1.x", "--root", str(self.root))
        self.assertEqual(code, 0, err)
        cl = self.read("CHANGELOG.md")
        self.assertLess(cl.index("## [0.2.0]"), cl.index("## [0.1.1]"))
        self.assertLess(cl.index("## [0.1.1]"), cl.index("## [0.1.0]"))
        self.assertIn("## [0.1.1] - 2026-12-01\n\n### Fixed\n\n- A crash.", cl)
        self.assertEqual(run("carry", "0.1.1", "--from", "support/0.1.x", "--root", str(self.root))[0], 1)

    def test_tag_source_writes_nothing(self):
        make(self.root, sources="tag")
        code, _, err = run("prepare", "0.2.0", "--date", "2026-11-26", "--root", str(self.root))
        self.assertEqual(code, 0, err)
        self.assertIn("## [0.2.0] - 2026-11-26", self.read("CHANGELOG.md"))
        self.assertEqual(self.read("VERSION"), "0.1.0\n")


if __name__ == "__main__":
    unittest.main()
