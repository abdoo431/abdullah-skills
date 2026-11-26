import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import ver_changelog as cl  # noqa: E402
from ver_semver import Version  # noqa: E402

V = Version.parse

BASE = """# Changelog

## [Unreleased]

### Added

- Workspace export.
- A long entry
  that spans two lines.

## [0.1.0] - 2026-11-03

### Added

- First release.

[Unreleased]: https://github.com/o/r/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/o/r/releases/tag/v0.1.0
"""

CUT = """# Changelog

## [Unreleased]

## [0.2.0] - 2026-11-26

### Added

- Workspace export.
- A long entry
  that spans two lines.

## [0.1.0] - 2026-11-03

### Added

- First release.

[Unreleased]: https://github.com/o/r/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/o/r/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/o/r/releases/tag/v0.1.0
"""


class ChangelogTests(unittest.TestCase):
    def test_sections_and_unreleased(self):
        secs = cl.sections(BASE)
        self.assertEqual([s.title for s in secs], ["Unreleased", "0.1.0"])
        self.assertEqual(secs[1].version, V("0.1.0"))
        self.assertEqual(secs[1].date, "2026-11-03")
        self.assertEqual(secs[0].line, 3)
        added = cl.unreleased(BASE)["Added"]
        self.assertEqual(added[0], "- Workspace export.")
        self.assertEqual(added[1], "- A long entry\n  that spans two lines.")

    def test_cut_moves_entries_and_links(self):
        self.assertEqual(cl.cut(BASE, V("0.2.0"), "2026-11-26", "v0.1.0", "v{version}"), CUT)

    def test_cut_first_release_link(self):
        text = "# Changelog\n\n## [Unreleased]\n\n### Added\n\n- A.\n\n[Unreleased]: https://github.com/o/r/compare/HEAD...HEAD\n"
        out = cl.cut(text, V("0.1.0"), "2026-11-26", None, "v{version}")
        self.assertIn("[Unreleased]: https://github.com/o/r/compare/v0.1.0...HEAD\n", out)
        self.assertIn("[0.1.0]: https://github.com/o/r/releases/tag/v0.1.0\n", out)

    def test_cut_without_links_adds_none(self):
        text = "# Changelog\n\n## Unreleased\n\n### Fixed\n\n- B.\n"
        out = cl.cut(text, V("0.1.1"), "2026-11-26", "v0.1.0", "v{version}")
        self.assertEqual(out, "# Changelog\n\n## Unreleased\n\n## 0.1.1 - 2026-11-26\n\n### Fixed\n\n- B.\n")

    def test_cut_unbracketed_heading_and_empty_subsection(self):
        text = "# Changelog\n\n## unreleased\n\n### Added\n\n### Fixed\n\n- B.\n\n## 0.1.0 - 2026-11-03\n\n- Old.\n"
        out = cl.cut(text, V("0.1.1"), "2026-11-26", "v0.1.0", "v{version}")
        self.assertEqual([s.title for s in cl.sections(out)], ["Unreleased", "0.1.1", "0.1.0"])
        self.assertEqual(cl.unreleased(out), {})
        self.assertEqual(cl.sections(out)[1].entries["Fixed"], ["- B."])

    def test_cut_refuses_empty(self):
        text = "# Changelog\n\n## [Unreleased]\n\n### Added\n\n## [0.1.0] - 2026-11-03\n\n- Old.\n"
        with self.assertRaises(ValueError) as cm:
            cl.cut(text, V("0.2.0"), "2026-11-26", "v0.1.0", "v{version}")
        self.assertEqual(str(cm.exception), "[Unreleased] has no entries to release")

    def test_fold_into_open_section(self):
        text = ("# Changelog\n\n## [Unreleased]\n\n### Fixed\n\n- b\n\n"
                "## [0.2.0] - 2026-11-26\n\n### Added\n\n- a\n\n## [0.1.0] - 2026-11-03\n\n- Old.\n")
        out = cl.fold_unreleased_into(text, V("0.2.0"))
        self.assertEqual(cl.unreleased(out), {})
        sec = [s for s in cl.sections(out) if s.title == "0.2.0"][0]
        self.assertEqual(list(sec.entries), ["Added", "Fixed"])
        self.assertEqual(sec.entries["Fixed"], ["- b"])
        self.assertEqual(cl.fold_unreleased_into(out, V("0.2.0")), out)

    def test_set_date_and_section_body(self):
        out = cl.set_date(CUT, V("0.2.0"), "2026-12-01")
        self.assertIn("## [0.2.0] - 2026-12-01\n", out)
        self.assertEqual(cl.section_body(CUT, V("0.1.0")), "### Added\n\n- First release.")

    def test_insert_section_by_version(self):
        text = "# Changelog\n\n## [Unreleased]\n\n## [0.2.0] - 2026-11-26\n\n- B.\n\n## [0.1.0] - 2026-11-03\n\n- A.\n"
        out = cl.insert_section(text, "## [0.1.1] - 2026-12-01\n\n### Fixed\n\n- C.", V("0.1.1"))
        self.assertEqual([s.title for s in cl.sections(out)], ["Unreleased", "0.2.0", "0.1.1", "0.1.0"])
        with self.assertRaises(ValueError):
            cl.insert_section(out, "## [0.2.0] - 2026-11-26\n\n- B.", V("0.2.0"))

    def test_insert_section_below_the_last_keeps_links_last(self):
        out = cl.insert_section(CUT, "## [0.0.9] - 2026-10-01\n\n- Z.", V("0.0.9"))
        self.assertEqual([s.title for s in cl.sections(out)], ["Unreleased", "0.2.0", "0.1.0", "0.0.9"])
        self.assertIn("- First release.\n\n## [0.0.9] - 2026-10-01\n\n- Z.\n\n[Unreleased]:", out)

    def test_problems(self):
        text = ("# Changelog\n\n## [Unreleased]\n\n## [0.1.0] - 2026-11-03\n\n- A.\n\n"
                "## [0.2.0] - 2026-11-26\n\n- B.\n\n## [0.2.0] - 2026-11-26\n\n- B.\n")
        probs = cl.problems(text)
        self.assertEqual(len(probs), 2)
        self.assertEqual({line for line, _ in probs}, {9, 13})
        self.assertEqual(cl.problems("# Changelog\n\n## [0.1.0] - 2026-11-03\n"), [(1, "no [Unreleased] section")])
        self.assertEqual(cl.problems(CUT), [])

    def test_fold_candidates(self):
        text = "## [Unreleased]\n\n## [0.2.0] - 2026-11-26\n\n### Added\n\n- a\n\n### Fixed\n\n- b\n"
        self.assertEqual(cl.fold_candidates(text, V("0.2.0")), ["- b"])
        self.assertEqual(cl.fold_candidates(CUT, V("0.1.0")), [])

    def test_crlf_and_bom_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "CHANGELOG.md"
            path.write_bytes(b"\xef\xbb\xbf" + CUT.replace("\n", "\r\n").encode("utf-8"))
            text, newline, bom = cl.read_text(path)
            self.assertEqual((newline, bom), ("\r\n", True))
            self.assertNotIn("\r", text)
            cl.write_text(path, cl.set_date(text, V("0.2.0"), "2026-12-01"), newline, bom)
            raw = path.read_bytes()
            self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
            self.assertIn(b"## [0.2.0] - 2026-12-01\r\n", raw)
            self.assertNotIn(b"\n", raw.replace(b"\r\n", b""))


if __name__ == "__main__":
    unittest.main()
