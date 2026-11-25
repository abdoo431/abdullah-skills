import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check_frontmatter  # noqa: E402


class FrontMatterTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def write_skill(self, text, folder="demo"):
        path = self.root / "skills" / folder / "SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_bytes(text.encode("utf-8"))
        return path

    def test_valid_skill_passes(self):
        path = self.write_skill("---\nname: demo\ndescription: Does a thing.\n---\nBody\n")
        self.assertEqual(check_frontmatter.check_skill(path), [])

    def test_valid_skill_with_crlf_passes(self):
        path = self.write_skill("---\r\nname: demo\r\ndescription: Does a thing.\r\n---\r\nBody\r\n")
        self.assertEqual(check_frontmatter.check_skill(path), [])

    def test_missing_front_matter(self):
        path = self.write_skill("# Just a heading\n")
        problems = check_frontmatter.check_skill(path)
        self.assertEqual(len(problems), 1)
        self.assertIn("no front matter", problems[0])

    def test_missing_description(self):
        path = self.write_skill("---\nname: demo\n---\n")
        problems = check_frontmatter.check_skill(path)
        self.assertEqual(len(problems), 1)
        self.assertIn("`description`", problems[0])

    def test_name_must_match_folder(self):
        path = self.write_skill("---\nname: other\ndescription: Does a thing.\n---\n")
        problems = check_frontmatter.check_skill(path)
        self.assertEqual(len(problems), 1)
        self.assertIn("does not match folder", problems[0])

    def test_unquoted_colon_space(self):
        path = self.write_skill("---\nname: demo\ndescription: Use when: always\n---\n")
        problems = check_frontmatter.check_skill(path)
        self.assertEqual(len(problems), 1)
        self.assertIn("quote", problems[0])

    def test_quoted_value_with_colon_passes(self):
        path = self.write_skill('---\nname: demo\ndescription: "Use when: always"\n---\n')
        self.assertEqual(check_frontmatter.check_skill(path), [])

    def test_empty_quoted_description(self):
        path = self.write_skill('---\nname: demo\ndescription: ""\n---\n')
        problems = check_frontmatter.check_skill(path)
        self.assertEqual(len(problems), 1)
        self.assertIn("`description`", problems[0])

    def test_empty_quoted_name(self):
        path = self.write_skill('---\nname: ""\ndescription: Does a thing.\n---\n')
        problems = check_frontmatter.check_skill(path)
        self.assertEqual(len(problems), 1)
        self.assertIn("`name`", problems[0])

    def test_cli_walks_nested_skills(self):
        self.write_skill("# nothing\n", folder="group/deep")
        script = str(SCRIPTS / "check_frontmatter.py")
        res = subprocess.run([sys.executable, script, "--root", str(self.root)],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 1)
        self.assertIn("skills/group/deep/SKILL.md: no front matter", res.stdout)

    def test_cli_missing_skills_folder(self):
        script = str(SCRIPTS / "check_frontmatter.py")
        res = subprocess.run([sys.executable, script, "--root", str(self.root)],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 2)
        self.assertIn("skills", res.stderr)

    def test_cli_exit_codes(self):
        self.write_skill("---\nname: demo\ndescription: Does a thing.\n---\n")
        script = str(SCRIPTS / "check_frontmatter.py")
        ok = subprocess.run([sys.executable, script, "--root", str(self.root)],
                            capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0)
        self.assertIn("All SKILL.md front matter parses.", ok.stdout)

        self.write_skill("# nothing\n", folder="bad")
        bad = subprocess.run([sys.executable, script, "--root", str(self.root)],
                             capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1)
        self.assertIn("skills/bad/SKILL.md: no front matter", bad.stdout)


if __name__ == "__main__":
    unittest.main()
