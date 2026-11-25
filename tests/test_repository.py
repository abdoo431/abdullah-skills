"""Tests that the repository's manifests and documents agree with each other."""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL_NAMES = sorted(p.parent.name for p in (REPO / "skills").glob("*/SKILL.md"))
FENCE_RE = re.compile(r"^```[^\n]*\n(.*?)^```", re.M | re.S)


def _read(path: Path) -> str:
    return path.read_bytes().decode("utf-8", errors="replace").replace("\r\n", "\n")


def _install_commands() -> list:
    block = _read(REPO / ".agents" / "install-block.md")
    return [line.strip() for fence in FENCE_RE.findall(block)
            for line in fence.splitlines() if line.strip()]


class RepositoryTests(unittest.TestCase):
    def test_plugin_skills_are_the_skill_folders(self):
        plugin = json.loads(_read(REPO / ".claude-plugin" / "plugin.json"))
        self.assertEqual(sorted(plugin["skills"]), [f"./skills/{name}" for name in SKILL_NAMES])

    def test_plugin_version_matches_the_changelog(self):
        plugin = json.loads(_read(REPO / ".claude-plugin" / "plugin.json"))
        released = re.search(r"^## \[(\d+\.\d+\.\d+)\]", _read(REPO / "CHANGELOG.md"), re.M)
        self.assertEqual(plugin["version"], released.group(1) if released else "0.1.0")

    def test_marketplace_lists_the_plugin(self):
        market = json.loads(_read(REPO / ".claude-plugin" / "marketplace.json"))
        self.assertEqual(market["name"], "abdullah")
        self.assertEqual([p["name"] for p in market["plugins"]], ["abdullah-skills"])

    def test_every_skill_is_linked_from_the_readme(self):
        readme = _read(REPO / "README.md")
        for name in SKILL_NAMES:
            with self.subTest(skill=name):
                self.assertIn(f"](skills/{name}/SKILL.md)", readme)

    def test_agent_instruction_files_are_identical(self):
        self.assertEqual((REPO / "CLAUDE.md").read_bytes(), (REPO / "AGENTS.md").read_bytes())

    def test_install_commands_appear_verbatim(self):
        commands = _install_commands()
        self.assertGreaterEqual(len(commands), 8)
        block = _read(REPO / ".agents" / "install-block.md").strip()
        for doc in ("README.md", "CLAUDE.md"):
            text = _read(REPO / doc)
            for command in commands:
                with self.subTest(doc=doc, command=command):
                    self.assertIn(command, text)
            with self.subTest(doc=doc, whole_block=True):
                self.assertIn(block, text)

    def test_documentation_check_passes(self):
        res = subprocess.run(
            [sys.executable, str(REPO / "skills" / "abdullah-docs" / "scripts" / "check_docs.py"),
             "--root", str(REPO), "--all", "--policy", "docs/DOCUMENTATION.md"],
            capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)


if __name__ == "__main__":
    unittest.main()
