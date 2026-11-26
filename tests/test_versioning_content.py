"""Tests for the text of the abdullah-versioning and setup-abdullah-versioning skills."""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
VER_SKILL = SKILLS / "abdullah-versioning"
VER_SETUP = SKILLS / "setup-abdullah-versioning"
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(VER_SKILL / "scripts"))

import check_frontmatter  # noqa: E402
import ver_policy  # noqa: E402
import version  # noqa: E402


def _read(path: Path) -> str:
    return path.read_bytes().decode("utf-8", errors="replace").replace("\r\n", "\n")


def _front_matter(path: Path) -> str:
    lines = _read(path).splitlines()
    end = lines.index("---", 1)
    return "\n".join(lines[1:end])


def _markdown(*folders: Path) -> list:
    return sorted(p for folder in folders for p in folder.rglob("*.md"))


class VersioningContentTests(unittest.TestCase):
    def test_versioning_front_matter(self):
        for skill in (VER_SKILL, VER_SETUP):
            with self.subTest(skill=skill.name):
                self.assertEqual(check_frontmatter.check_skill(skill / "SKILL.md"), [])

    def test_setup_versioning_is_user_invoked_only(self):
        self.assertRegex(_front_matter(VER_SETUP / "SKILL.md"), r"(?m)^disable-model-invocation:\s*true\s*$")
        self.assertRegex(_read(VER_SETUP / "agents" / "openai.yaml"), r"(?m)^\s+allow_implicit_invocation:\s*false\s*$")

    def test_versioning_skill_is_model_invoked(self):
        self.assertNotIn("disable-model-invocation", _front_matter(VER_SKILL / "SKILL.md"))
        self.assertNotIn("allow_implicit_invocation", _read(VER_SKILL / "agents" / "openai.yaml"))

    def test_versioning_links_resolve(self):
        with tempfile.TemporaryDirectory() as tmp:
            for skill in (VER_SKILL, VER_SETUP):
                shutil.copytree(skill, Path(tmp) / "skills" / skill.name,
                                ignore=shutil.ignore_patterns("__pycache__"))
            res = subprocess.run(
                [sys.executable, str(SKILLS / "abdullah-docs" / "scripts" / "check_docs.py"), "--root", tmp, "--all"],
                capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 2, res.stderr)
        broken = [line for line in res.stdout.splitlines() if ": error: link:" in line]
        self.assertEqual(broken, [])

    def test_versioning_names_no_single_agent_tool(self):
        names = re.compile(r"\b(Bash tool|Read tool|Write tool|Edit tool|TodoWrite|Grep tool|Glob tool)\b")
        for path in _markdown(VER_SKILL, VER_SETUP):
            with self.subTest(path=path.relative_to(REPO).as_posix()):
                self.assertIsNone(names.search(_read(path)))

    def test_versioning_skill_stays_short(self):
        self.assertLess(len(_read(VER_SKILL / "SKILL.md").splitlines()), 200)

    def test_versioning_agent_section_matches_design(self):
        design = _read(REPO / "docs" / "design" / "2026-11-26-abdullah-versioning-design.md")
        section = design.split("\n### 6.4", 1)[1].split("\n## 7.", 1)[0]
        block = re.search(r"^```\n(.*?)^```", section, re.M | re.S).group(1)
        expected = block.replace("<policy path>", "{policy}").replace("<integration branch>", "{integration}")
        template = _read(VER_SKILL / "templates" / "agent-section.md")
        self.assertEqual(template.splitlines()[0], ver_policy.AGENT_SECTION_HEADING)
        self.assertEqual(template, expected)

    def test_releasing_template_block_parses(self):
        template = VER_SKILL / "templates" / "releasing.md"
        self.assertRegex(_read(template), r"(?m)^```abdullah-versioning\s*$")
        settings = ver_policy.read_settings(template)
        self.assertIn(settings.layout, ver_policy.LAYOUTS)

    def test_reference_commands_exist(self):
        used = set()
        for path in _markdown(VER_SKILL, VER_SETUP):
            used |= set(re.findall(r"version\.py (\w+)", _read(path)))
        self.assertTrue(used)
        self.assertLessEqual(used, set(version.COMMANDS))


if __name__ == "__main__":
    unittest.main()
