import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import ver_policy  # noqa: E402
import ver_survey  # noqa: E402
from ver_semver import Version  # noqa: E402

from .fixtures import Repo  # noqa: E402

V = Version.parse


def changelog(*versions: str, unreleased: str = "") -> str:
    parts = ["# Changelog", "", "## [Unreleased]", ""]
    if unreleased:
        parts += [unreleased, ""]
    for v in versions:
        parts += [f"## [{v}] - 2026-11-0{len(parts) % 9 + 1}", "", "### Added", "", f"- Release {v}.", ""]
    return "\n".join(parts)


def props(v: str) -> str:
    return f"<Project>\n  <PropertyGroup>\n    <Version>{v}</Version>\n  </PropertyGroup>\n</Project>\n"


def package(v: str, name: str = "web") -> str:
    return f'{{\n  "name": "{name}",\n  "version": "{v}"\n}}\n'


def released_dev_main(repo: Repo) -> None:
    """tags v0.1.0 and v0.2.0 on main, a stray tag, and dev declaring 0.3.0-dev."""
    repo.write("Directory.Build.props", props("0.1.0"))
    repo.write("src/web/package.json", package("0.1.0"))
    repo.write("CHANGELOG.md", changelog("0.1.0"))
    repo.commit("release 0.1.0")
    repo.tag("v0.1.0")
    repo.write("Directory.Build.props", props("0.2.0"))
    repo.write("src/web/package.json", package("0.2.0"))
    repo.write("CHANGELOG.md", changelog("0.2.0", "0.1.0"))
    repo.commit("release 0.2.0")
    repo.tag("v0.2.0")
    repo.tag("plan1-pre-squash")
    repo.branch("dev")
    repo.write("Directory.Build.props", props("0.3.0-dev"))
    repo.write("src/web/package.json", package("0.3.0-dev"))
    repo.commit("declare 0.3.0-dev")


class SurveyTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Repo(Path(self._tmp.name))
        self.root = self.repo.root

    def tearDown(self):
        self._tmp.cleanup()

    def test_new_project(self):
        self.repo.write("pyproject.toml", '[project]\nname = "x"\nversion = "0.1.0"\n')
        self.repo.write("CHANGELOG.md", changelog(unreleased="### Added\n\n- A."))
        self.repo.commit("init")
        s = ver_survey.survey(self.root)
        self.assertEqual((s.verdict, s.current, s.layout), ("new", None, "main"))
        self.assertEqual(s.sources, [("pyproject.toml", "0.1.0")])
        self.assertTrue(s.has_unreleased)
        self.assertEqual(s.stops, [])

    def test_released_dev_main_project(self):
        released_dev_main(self.repo)
        s = ver_survey.survey(self.root)
        self.assertEqual((s.verdict, s.current, s.layout), ("released", "0.2.0", "dev-main"))
        self.assertEqual(s.roles, {"production": "main", "staging": None, "integration": "dev"})
        self.assertEqual(s.tags, ["v0.1.0", "v0.2.0"])
        self.assertEqual(s.tag_format, "v{version}")
        self.assertEqual(s.stray_tags, ["plan1-pre-squash"])
        self.assertFalse(s.non_semver)
        self.assertEqual(s.released, ["0.2.0", "0.1.0"])
        self.assertEqual(s.stops, [])
        data = json.loads(s.to_json())
        self.assertEqual(data["current"], "0.2.0")

    def test_default_branch_is_not_production(self):
        released_dev_main(self.repo)
        self.repo.run("update-ref", "refs/remotes/origin/dev", "HEAD")
        self.repo.run("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/dev")
        self.assertEqual(ver_survey.survey(self.root).roles["production"], "main")

    def test_stop_when_files_and_tag_disagree(self):
        self.repo.write("VERSION", "0.2.0\n")
        self.repo.write("CHANGELOG.md", changelog("0.2.0"))
        self.repo.commit("x")
        self.repo.tag("v0.2.0")
        self.repo.write("VERSION", "0.3.0\n")
        self.repo.commit("y")
        s = ver_survey.survey(self.root)
        self.assertEqual(len(s.stops), 1)
        self.assertIn("disagree", s.stops[0])

    def test_stop_on_non_semver_tags(self):
        self.repo.write("VERSION", "2024.06\n")
        self.repo.commit("x")
        self.repo.tag("2024.05")
        self.repo.tag("2024.06")
        s = ver_survey.survey(self.root)
        self.assertTrue(s.non_semver)
        self.assertEqual(s.verdict, "ambiguous")
        self.assertTrue(any("SemVer" in stop for stop in s.stops))

    def test_stop_on_releases_without_tags(self):
        self.repo.write("VERSION", "0.2.0\n")
        self.repo.write("CHANGELOG.md", changelog("0.2.0", "0.1.0"))
        self.repo.commit("x")
        s = ver_survey.survey(self.root)
        self.assertEqual((s.verdict, s.current), ("released", "0.2.0"))
        self.assertTrue(any("no tags" in stop for stop in s.stops))

    def test_stop_on_a_monorepo(self):
        self.repo.write("apps/a/package.json", package("1.2.0", "a"))
        self.repo.write("apps/b/package.json", package("0.4.0", "b"))
        self.repo.commit("x")
        s = ver_survey.survey(self.root)
        self.assertEqual(s.verdict, "ambiguous")
        self.assertTrue(any("monorepo" in stop for stop in s.stops))

    def test_master_and_support(self):
        self.repo.write("VERSION", "0.1.0\n")
        self.repo.commit("x")
        self.repo.tag("v0.1.0")
        self.repo.run("branch", "-m", "master")
        self.repo.run("branch", "support/0.1.x")
        s = ver_survey.survey(self.root)
        self.assertEqual(s.roles["production"], "master")
        self.assertEqual(s.support, ["support/0.1.x"])

    def _status(self, unreleased: str) -> ver_survey.Status:
        released_dev_main(self.repo)
        self.repo.write("CHANGELOG.md", changelog("0.2.0", "0.1.0", unreleased=unreleased))
        settings = ver_policy.Settings(layout="dev-main",
                                       sources=["Directory.Build.props", "src/web/package.json"])
        return ver_survey.status(self.root, settings)

    def test_status_reports_the_branch_and_versions(self):
        st = self._status("")
        self.assertEqual((st.branch, st.role, st.latest), ("dev", "integration", V("0.2.0")))
        self.assertEqual(st.declared, {"Directory.Build.props": "0.3.0-dev", "src/web/package.json": "0.3.0-dev"})
        self.assertTrue(st.agree)
        self.assertEqual(st.changelog_latest, "0.2.0")
        self.assertIsNone(st.due)

    def test_status_due(self):
        self.assertEqual(self._status("### Security\n\n- Patch a hole.").due, "patch: Security")

    def test_status_due_minor(self):
        self.assertEqual(self._status("### Added\n\n- A.").due, "minor when the milestone is finished: Added")

    def test_status_support_branch_latest_is_of_its_line(self):
        released_dev_main(self.repo)
        self.repo.checkout("main")
        self.repo.run("checkout", "-q", "-b", "support/0.1.x", "v0.1.0")
        st = ver_survey.status(self.root, ver_policy.Settings(layout="dev-main", sources=["Directory.Build.props"]))
        self.assertEqual((st.role, st.latest), ("support", V("0.1.0")))

    def test_plain_folder(self):
        with tempfile.TemporaryDirectory() as plain:
            root = Path(plain)
            (root / "VERSION").write_text("0.1.0\n", encoding="utf-8")
            s = ver_survey.survey(root)
            self.assertFalse(s.git)
            self.assertEqual(s.sources, [("VERSION", "0.1.0")])
            self.assertEqual([f.kind for f in s.findings], ["git"])
            st = ver_survey.status(root, ver_policy.Settings(layout="main", sources=["VERSION"]))
            self.assertEqual([f.kind for f in st.findings], ["git"])
            self.assertIsNone(st.role)

    def test_detached_head(self):
        released_dev_main(self.repo)
        self.repo.detach()
        st = ver_survey.status(self.root, ver_policy.Settings(layout="dev-main", sources=["Directory.Build.props"]))
        self.assertIsNone(st.branch)
        self.assertIsNone(st.role)


if __name__ == "__main__":
    unittest.main()
