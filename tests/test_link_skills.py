"""Tests for scripts/link_skills.py.

Every test runs a copy of the script and the skills in a temporary folder, with every
--dest inside temporary folders, so no test touches a real agent skill directory or the
working copy's own skills.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL_NAMES = sorted(p.parent.name for p in (REPO / "skills").glob("*/SKILL.md"))


def _make_link(source: Path, target: Path) -> None:
    if os.name == "nt":
        import _winapi
        _winapi.CreateJunction(str(source), str(target))
    else:
        os.symlink(source, target, target_is_directory=True)


def _files_under(folder: Path) -> list:
    return sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file())


class LinkSkillsTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name).resolve()
        self.repo = self.tmp / "repo"
        (self.repo / "scripts").mkdir(parents=True)
        shutil.copy2(REPO / "scripts" / "link_skills.py", self.repo / "scripts" / "link_skills.py")
        shutil.copytree(REPO / "skills", self.repo / "skills",
                        ignore=shutil.ignore_patterns("__pycache__"))
        self.skill_files = _files_under(self.repo / "skills")
        self.dest_a = self.tmp / "agent-a" / "skills"
        self.dest_b = self.tmp / "agent-b" / "skills"

    def run_script(self, *args):
        return subprocess.run(
            [sys.executable, str(self.repo / "scripts" / "link_skills.py"), *args],
            capture_output=True, text=True)

    def link_both(self):
        return self.run_script("--dest", str(self.dest_a), "--dest", str(self.dest_b))

    def assert_linked(self, dest: Path):
        self.assertEqual(sorted(os.listdir(dest)), SKILL_NAMES)
        for name in SKILL_NAMES:
            entry = dest / name
            self.assertEqual(entry.resolve(), (self.repo / "skills" / name).resolve())
            self.assertTrue((entry / "SKILL.md").is_file())

    def test_links_every_skill_into_each_destination(self):
        res = self.link_both()
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assert_linked(self.dest_a)
        self.assert_linked(self.dest_b)
        for name in SKILL_NAMES:
            self.assertIn(f"linked {name} -> {self.dest_a.as_posix()}", res.stdout)

    def test_second_run_replaces_the_links(self):
        self.assertEqual(self.link_both().returncode, 0)
        res = self.link_both()
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assert_linked(self.dest_a)
        self.assert_linked(self.dest_b)
        self.assertEqual(_files_under(self.repo / "skills"), self.skill_files)

    def test_refuses_to_replace_a_real_folder(self):
        real = self.dest_a / SKILL_NAMES[0]
        real.mkdir(parents=True)
        (real / "keep.txt").write_text("mine", encoding="utf-8")
        res = self.run_script("--dest", str(self.dest_a))
        self.assertEqual(res.returncode, 1)
        self.assertIn(real.as_posix(), res.stderr)
        self.assertEqual(os.listdir(real), ["keep.txt"])
        self.assertEqual((real / "keep.txt").read_text(encoding="utf-8"), "mine")

    def test_refuses_a_destination_inside_the_repository(self):
        inside = self.repo / "local-skills"
        res = self.run_script("--dest", str(self.dest_a), "--dest", str(inside))
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("inside the repository", res.stderr)
        self.assertFalse(inside.exists())
        self.assertFalse(self.dest_a.exists())
        res = self.run_script("--dest", str(self.repo / "skills"))
        self.assertNotEqual(res.returncode, 0)
        self.assertEqual(_files_under(self.repo / "skills"), self.skill_files)

    def test_remove_deletes_the_links_and_keeps_the_skills(self):
        self.assertEqual(self.link_both().returncode, 0)
        res = self.run_script("--dest", str(self.dest_a), "--dest", str(self.dest_b), "--remove")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(os.listdir(self.dest_a), [])
        self.assertEqual(os.listdir(self.dest_b), [])
        self.assertEqual(_files_under(self.repo / "skills"), self.skill_files)

    def foreign_link(self) -> tuple:
        elsewhere = self.tmp / "elsewhere" / SKILL_NAMES[0]
        elsewhere.mkdir(parents=True)
        (elsewhere / "theirs.txt").write_text("theirs", encoding="utf-8")
        self.dest_a.mkdir(parents=True)
        link = self.dest_a / SKILL_NAMES[0]
        _make_link(elsewhere, link)
        return link, elsewhere

    def test_remove_leaves_a_link_to_another_folder(self):
        link, elsewhere = self.foreign_link()
        res = self.run_script("--dest", str(self.dest_a), "--remove")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn(link.as_posix(), res.stdout)
        self.assertEqual(link.resolve(), elsewhere.resolve())
        self.assertEqual(os.listdir(self.dest_a), [SKILL_NAMES[0]])
        self.assertEqual(os.listdir(elsewhere), ["theirs.txt"])

    def test_does_not_replace_a_link_to_another_folder(self):
        link, elsewhere = self.foreign_link()
        res = self.run_script("--dest", str(self.dest_a))
        self.assertEqual(res.returncode, 1)
        self.assertIn(link.as_posix(), res.stderr)
        self.assertEqual(link.resolve(), elsewhere.resolve())
        for name in SKILL_NAMES[1:]:
            self.assertEqual((self.dest_a / name).resolve(), (self.repo / "skills" / name).resolve())

    def test_an_os_error_is_reported_and_the_rest_continue(self):
        not_a_folder = self.tmp / "a-file"
        not_a_folder.write_text("", encoding="utf-8")
        res = self.run_script("--dest", str(not_a_folder), "--dest", str(self.dest_b))
        self.assertEqual(res.returncode, 1)
        for name in SKILL_NAMES:
            self.assertIn(f"error: {not_a_folder.as_posix()}/{name}: ", res.stderr)
        self.assertNotIn("Traceback", res.stderr)
        self.assert_linked(self.dest_b)

    def test_dry_run_changes_nothing(self):
        res = self.run_script("--dest", str(self.dest_a), "--dry-run")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn(self.dest_a.as_posix(), res.stdout)
        self.assertFalse(self.dest_a.exists())


if __name__ == "__main__":
    unittest.main()
