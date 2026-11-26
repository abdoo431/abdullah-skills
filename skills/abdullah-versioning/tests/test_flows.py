"""Each release flow of design §7, played end to end the way the agent runs it."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import ver_changelog  # noqa: E402

from .fixtures import Repo  # noqa: E402
from .test_cli_read import run  # noqa: E402

DATE = "2026-11-26"
START = """# Changelog

## [Unreleased]

## [0.1.0] - 2026-11-03

### Added

- First release.
"""


class Flow:
    def __init__(self, root: Path, layout: str, source: str = "VERSION"):
        self.repo = Repo(root)
        self.root = root
        self.source = source
        self.repo.write(source, '{\n  "name": "p",\n  "version": "0.1.0"\n}\n' if source.endswith(".json") else "0.1.0\n")
        self.repo.write("CHANGELOG.md", START)
        self.repo.write("docs/RELEASING.md",
                        f"```abdullah-versioning\nlayout: {layout}\nsources: {source}\n```\n")
        self.repo.commit("init")
        self.repo.tag("v0.1.0")

    # the agent's moves -------------------------------------------------------------
    def v(self, *argv: str) -> str:
        code, out, err = run(*argv, "--root", str(self.root))
        assert code == 0, f"version.py {' '.join(argv)} failed: {err}{out}"
        return out

    def git(self, *args: str):
        proc = self.repo.run(*args)
        assert proc.returncode == 0, f"git {' '.join(args)} failed: {proc.stderr}"
        return proc

    def entry(self, subsection: str, text: str) -> None:
        cl = self.read("CHANGELOG.md")
        cl = cl.replace("## [Unreleased]\n", f"## [Unreleased]\n\n### {subsection}\n\n- {text}\n", 1)
        self.repo.write("CHANGELOG.md", cl)

    def work(self, base: str, name: str, subsection: str, text: str, into: str = "") -> None:
        """A work branch from base with one changelog entry, squash-merged into `into` (default base).

        With into == name the branch is left checked out, unmerged (a hotfix branch still to cut).
        """
        self.repo.checkout(base)
        self.repo.branch(name)
        self.entry(subsection, text)
        self.repo.commit(name)
        if into != name:
            self.squash(name, into or base)

    def squash(self, branch: str, into: str) -> None:
        self.repo.checkout(into)
        self.git("merge", "--squash", branch)
        self.repo.commit(f"squash {branch}")

    def merge(self, branch: str, into: str) -> None:
        self.repo.checkout(into)
        self.git("merge", "--no-ff", "--no-edit", branch)

    def branch_from(self, base: str, name: str) -> None:
        self.repo.checkout(base)
        self.repo.branch(name)

    def back_merge(self, source: str, into: str, own_version: str) -> None:
        """§7.6: merge source into into; resolve version files and the changelog mechanically."""
        self.repo.checkout(into)
        merged = self.repo.run("merge", "--no-ff", "--no-edit", source).returncode == 0
        if not merged:
            conflicted = self.git("diff", "--name-only", "--diff-filter=U").stdout.split()
            for path in conflicted:
                self.git("checkout", "--ours", path)
            if "CHANGELOG.md" in conflicted:
                theirs = self.repo.run("show", f"{source}:CHANGELOG.md").stdout
                ours = self.read("CHANGELOG.md")
                have = {s.version for s in ver_changelog.sections(ours) if s.version}
                for sec in ver_changelog.sections(theirs):
                    if sec.version and sec.version not in have:
                        self.v("carry", str(sec.version), "--from", source)
        self.v("declare", own_version, "--allow-long-lived")
        self.git("add", "-A")
        if not merged:
            self.git("commit", "--no-edit")
        elif self.git("status", "--porcelain").stdout.strip():
            self.repo.commit(f"declare {own_version} after merging {source}")

    # what the tests look at --------------------------------------------------------
    def read(self, rel: str) -> str:
        return (self.root / rel).read_text(encoding="utf-8")

    def declared(self, branch: str) -> str:
        self.repo.checkout(branch)
        text = self.read(self.source)
        return text.split('"version": "')[1].split('"')[0] if self.source.endswith(".json") else text.strip()

    def check(self, *branches: str) -> None:
        for b in branches:
            self.repo.checkout(b)
            code, out, err = run("check", "--root", str(self.root))
            assert code == 0, f"check on {b}: {out}{err}"

    def tags(self) -> list:
        return self.git("tag", "--list").stdout.split()

    def tag_on(self, tag: str, branch: str) -> bool:
        return branch in self.git("branch", "--contains", tag, "--format=%(refname:short)").stdout.split()


class FlowTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _open_dev(self, f: Flow, version: str) -> None:
        f.branch_from("dev", f"release/{version}")
        f.v("declare", version)
        f.repo.commit(f"declare {version}")
        f.squash(f"release/{version}", "dev")

    def test_dev_staging_main(self):
        f = Flow(self.root, "dev-staging-main")
        f.git("branch", "staging")
        f.git("branch", "dev")
        self._open_dev(f, "0.2.0-dev")
        f.work("dev", "feature/export", "Added", "Export.")

        f.branch_from("dev", "release/0.2.0")
        f.v("prepare", "0.2.0", "--pre", "rc", "--date", DATE)
        f.repo.commit("cut 0.2.0")
        f.merge("release/0.2.0", "staging")
        f.repo.tag("v0.2.0-rc.1")
        f.back_merge("staging", "dev", "0.3.0-dev")
        f.work("dev", "feature/next", "Added", "Next.")

        f.work("staging", "fix/crash", "Fixed", "A crash.")
        f.branch_from("staging", "release/0.2.0-rc.2")
        f.v("declare", "0.2.0-rc.2")
        f.repo.commit("declare 0.2.0-rc.2")
        f.merge("release/0.2.0-rc.2", "staging")
        f.repo.tag("v0.2.0-rc.2")
        f.back_merge("staging", "dev", "0.3.0-dev")

        f.branch_from("staging", "release/0.2.0-final")
        f.v("declare", "0.2.0", "--date", DATE)
        f.repo.commit("declare 0.2.0")
        f.merge("release/0.2.0-final", "staging")
        f.merge("staging", "main")
        f.repo.tag("v0.2.0")
        f.back_merge("main", "dev", "0.3.0-dev")

        self.assertTrue(f.tag_on("v0.2.0-rc.1", "staging"))
        self.assertTrue(f.tag_on("v0.2.0-rc.2", "staging"))
        self.assertEqual(f.git("rev-parse", "v0.2.0^{commit}").stdout, f.git("rev-parse", "main").stdout)
        self.assertFalse([t for t in f.tags() if "dev" in t])
        self.assertEqual(f.declared("dev"), "0.3.0-dev")
        self.assertEqual(ver_changelog.unreleased(f.read("CHANGELOG.md")), {"Added": ["- Next."]})
        f.repo.checkout("main")
        released = [s for s in ver_changelog.sections(f.read("CHANGELOG.md")) if s.title == "0.2.0"][0]
        self.assertEqual(released.entries, {"Added": ["- Export."], "Fixed": ["- A crash."]})
        f.check("dev", "staging", "main")

    def test_dev_main(self):
        f = Flow(self.root, "dev-main")
        f.git("branch", "dev")
        self._open_dev(f, "0.2.0-dev")
        f.work("dev", "feature/export", "Added", "Export.")
        f.branch_from("dev", "release/0.2.0")
        f.v("prepare", "0.2.0", "--date", DATE)
        f.repo.commit("cut 0.2.0")
        f.squash("release/0.2.0", "dev")
        f.merge("dev", "main")
        f.repo.tag("v0.2.0")
        self._open_dev(f, "0.3.0-dev")
        f.check("dev", "main")

        f.work("dev", "feature/more", "Added", "More.")
        f.branch_from("dev", "release/0.3.0")
        f.v("prepare", "0.3.0", "--pre", "rc", "--date", DATE)
        f.repo.commit("cut 0.3.0")
        f.repo.tag("v0.3.0-rc.1")
        f.entry("Fixed", "A crash.")
        f.v("declare", "0.3.0-rc.2")
        f.repo.commit("rc.2")
        f.repo.tag("v0.3.0-rc.2")
        f.v("declare", "0.3.0", "--date", DATE)
        f.repo.commit("0.3.0")
        f.squash("release/0.3.0", "dev")
        f.merge("dev", "main")
        f.repo.tag("v0.3.0")
        self._open_dev(f, "0.4.0-dev")
        self.assertEqual(f.declared("main"), "0.3.0")
        f.check("dev", "main")

    def test_main_only(self):
        f = Flow(self.root, "main", source=".claude-plugin/plugin.json")
        f.work("main", "feature/export", "Added", "Export.")
        f.check("main")
        f.branch_from("main", "release/0.2.0")
        f.v("prepare", "0.2.0", "--date", DATE)
        f.repo.commit("cut 0.2.0")
        f.merge("release/0.2.0", "main")
        f.repo.tag("v0.2.0")
        f.work("main", "feature/next", "Added", "Next.")
        self.assertEqual(f.declared("main"), "0.2.0")
        f.check("main")

    def _staging_in_rc(self) -> Flow:
        """main at v0.2.0, staging at v0.3.0-rc.1, dev at 0.4.0-dev."""
        f = Flow(self.root, "dev-staging-main")
        f.git("branch", "staging")
        f.git("branch", "dev")
        for version, entry in (("0.2.0", "Export."), ("0.3.0", "More.")):
            f.work("dev", f"feature/{version}", "Added", entry)
            f.branch_from("dev", f"release/{version}")
            f.v("prepare", version, "--pre", "rc", "--date", DATE)
            f.repo.commit(f"cut {version}")
            f.merge(f"release/{version}", "staging")
            f.repo.tag(f"v{version}-rc.1")
            if version == "0.2.0":
                f.branch_from("staging", "release/0.2.0-final")
                f.v("declare", "0.2.0", "--date", DATE)
                f.repo.commit("0.2.0")
                f.merge("release/0.2.0-final", "staging")
                f.merge("staging", "main")
                f.repo.tag("v0.2.0")
            f.back_merge("staging", "dev", "0.4.0-dev" if version == "0.3.0" else "0.3.0-dev")
        return f

    def test_hotfix_with_back_merges(self):
        f = self._staging_in_rc()
        f.work("main", "hotfix/0.2.1-crash", "Fixed", "A crash.", into="hotfix/0.2.1-crash")
        f.v("prepare", "0.2.1", "--date", "2026-12-02")
        f.repo.commit("0.2.1")
        f.merge("hotfix/0.2.1-crash", "main")
        f.repo.tag("v0.2.1")
        f.back_merge("main", "staging", "0.3.0-rc.1")
        f.back_merge("main", "dev", "0.4.0-dev")
        self.assertEqual(f.declared("staging"), "0.3.0-rc.1")
        self.assertEqual(f.declared("dev"), "0.4.0-dev")
        titles = [s.title for s in ver_changelog.sections(f.read("CHANGELOG.md"))]
        self.assertEqual(titles, ["Unreleased", "0.3.0", "0.2.1", "0.2.0", "0.1.0"])
        f.check("main", "staging", "dev")

    def test_back_merge_conflict_resolution(self):
        f = Flow(self.root, "dev-main")
        f.git("branch", "dev")
        self._open_dev(f, "0.2.0-dev")
        f.work("main", "hotfix/0.1.1-crash", "Fixed", "A crash.", into="hotfix/0.1.1-crash")
        f.v("prepare", "0.1.1", "--date", DATE)
        f.repo.commit("0.1.1")
        f.merge("hotfix/0.1.1-crash", "main")
        f.repo.tag("v0.1.1")
        f.repo.checkout("dev")
        self.assertNotEqual(f.repo.run("merge", "--no-ff", "--no-edit", "main").returncode, 0)
        f.git("checkout", "--theirs", "VERSION")
        code, out, _ = run("check", "--root", str(self.root))
        self.assertEqual(code, 1)
        self.assertIn(": error: role:", out)
        f.v("declare", "0.2.0-dev", "--allow-long-lived")
        f.git("add", "-A")
        f.git("commit", "--no-edit")
        self.assertEqual(f.declared("dev"), "0.2.0-dev")
        f.check("dev", "main")

    def test_support_line(self):
        f = Flow(self.root, "main")
        f.work("main", "feature/export", "Added", "Export.")
        f.branch_from("main", "release/0.2.0")
        f.v("prepare", "0.2.0", "--date", DATE)
        f.repo.commit("0.2.0")
        f.merge("release/0.2.0", "main")
        f.repo.tag("v0.2.0")
        f.git("checkout", "-q", "-b", "support/0.1.x", "v0.1.0")
        f.work("support/0.1.x", "hotfix/0.1.1-crash", "Fixed", "A crash.", into="hotfix/0.1.1-crash")
        f.v("prepare", "0.1.1", "--date", "2026-12-02")
        f.repo.commit("0.1.1")
        f.merge("hotfix/0.1.1-crash", "support/0.1.x")
        f.repo.tag("v0.1.1")
        self.assertTrue(f.tag_on("v0.1.1", "support/0.1.x"))
        self.assertFalse(f.tag_on("v0.1.1", "main"))
        f.check("support/0.1.x")
        f.repo.checkout("main")
        f.v("carry", "0.1.1", "--from", "support/0.1.x")
        f.repo.commit("carry 0.1.1")
        titles = [s.title for s in ver_changelog.sections(f.read("CHANGELOG.md"))]
        self.assertEqual(titles, ["Unreleased", "0.2.0", "0.1.1", "0.1.0"])
        f.check("main")


if __name__ == "__main__":
    unittest.main()
