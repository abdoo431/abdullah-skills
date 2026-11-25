import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
DOCS_SKILL = SKILLS / "abdullah-docs"
SETUP_SKILL = SKILLS / "setup-abdullah-docs"
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(DOCS_SKILL / "scripts"))

import check_frontmatter  # noqa: E402
import docs_policy  # noqa: E402


def _read(path: Path) -> str:
    return path.read_bytes().decode("utf-8", errors="replace")


def _front_matter(path: Path) -> str:
    lines = _read(path).splitlines()
    end = lines.index("---", 1)
    return "\n".join(lines[1:end])


class SkillContentTests(unittest.TestCase):
    def test_front_matter_passes_for_both_skills(self):
        for skill in (DOCS_SKILL, SETUP_SKILL):
            with self.subTest(skill=skill.name):
                self.assertEqual(check_frontmatter.check_skill(skill / "SKILL.md"), [])

    def test_setup_skill_is_user_invoked_only(self):
        self.assertRegex(_front_matter(SETUP_SKILL / "SKILL.md"),
                         r"(?m)^disable-model-invocation:\s*true\s*$")
        self.assertRegex(_read(SETUP_SKILL / "agents" / "openai.yaml"),
                         r"(?m)^\s+allow_implicit_invocation:\s*false\s*$")

    def test_docs_skill_is_model_invoked(self):
        self.assertNotIn("disable-model-invocation", _front_matter(DOCS_SKILL / "SKILL.md"))
        self.assertNotIn("allow_implicit_invocation", _read(DOCS_SKILL / "agents" / "openai.yaml"))

    def test_relative_links_in_skills_resolve(self):
        # A copy outside git: check_docs walks every file instead of only tracked ones,
        # and a link that leaves the skills folder fails, as it would in an installed copy.
        with tempfile.TemporaryDirectory() as tmp:
            for skill in (DOCS_SKILL, SETUP_SKILL):
                shutil.copytree(skill, Path(tmp) / "skills" / skill.name,
                                ignore=shutil.ignore_patterns("__pycache__"))
            res = subprocess.run(
                [sys.executable, str(DOCS_SKILL / "scripts" / "check_docs.py"), "--root", tmp, "--all"],
                capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 2, res.stderr)
        broken = [line for line in res.stdout.splitlines()
                  if line.startswith("skills/") and ": error: link:" in line]
        self.assertEqual(broken, [])

    def test_agent_section_template_starts_with_heading(self):
        text = _read(DOCS_SKILL / "templates" / "agent-section.md")
        self.assertEqual(text.splitlines()[0], docs_policy.AGENT_SECTION_HEADING)
        self.assertIn("{policy}", text)
        self.assertIn("https://github.com/abdoo431/abdullah-skills", text)

    def test_setup_reference_carries_a_parsable_settings_block(self):
        setup = DOCS_SKILL / "reference" / "setup.md"
        self.assertRegex(_read(setup), r"(?m)^```abdullah-docs\s*$")
        settings = docs_policy.read_settings(setup)
        self.assertEqual(settings.profile, "lean")
        self.assertEqual(settings.adr_dir, "docs/adr")
        self.assertEqual(settings.changelog, "CHANGELOG.md")
        self.assertEqual(settings.base, "origin/main")
        self.assertEqual(settings.history, ["docs/superpowers/plans/**", "conversations/**"])
        self.assertEqual(settings.pairs, [("docs/superpowers/specs/*-design.md",
                                           "docs/superpowers/specs/*-design.en.md")])
        self.assertEqual(settings.examples, ["README.md"])

    def test_docs_skill_stays_short(self):
        lines = _read(DOCS_SKILL / "SKILL.md").splitlines()
        self.assertLess(len(lines), 200)

    def test_skill_files_name_no_single_agent_tool(self):
        names = re.compile(r"\b(Bash tool|Read tool|Write tool|Edit tool|TodoWrite|Grep tool|Glob tool)\b")
        for path in sorted(list(DOCS_SKILL.rglob("*.md")) + list(SETUP_SKILL.rglob("*.md"))):
            with self.subTest(path=path.relative_to(REPO).as_posix()):
                self.assertIsNone(names.search(_read(path)))


if __name__ == "__main__":
    unittest.main()
