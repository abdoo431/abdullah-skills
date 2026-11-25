import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import docs_adr
from docs_adr import AdrFile


class AdrTests(unittest.TestCase):
    def test_adr_files_skips_template_and_other_files(self):
        files = docs_adr.adr_files(["0001-a.md", "0000-template.md", "README.md", "012-b.md"])
        self.assertEqual([f.number for f in files], [1, 12])

    def test_number_width(self):
        self.assertEqual(docs_adr.number_width([]), 4)
        self.assertEqual(docs_adr.number_width([AdrFile(1, "001-a.md")]), 3)

    def test_next_number_prefers_the_base_when_ahead(self):
        self.assertEqual(docs_adr.next_number([AdrFile(42, "0042-x.md")], [AdrFile(43, "0043-y.md")]), 44)
        self.assertEqual(docs_adr.next_number([], []), 1)

    def test_slugify(self):
        self.assertEqual(docs_adr.slugify("Use Postgres, not SQLite!"), "use-postgres-not-sqlite")
        slug = docs_adr.slugify("word " * 30)
        self.assertLessEqual(len(slug), 60)
        self.assertFalse(slug.endswith("-"))

    def test_table_row_is_appended_after_the_last_row(self):
        text = (
            "# ADRs\n\n| ADR | Decision | Status |\n|---|---|---|\n"
            "| [0001](0001-a.md) | A | Accepted |\n| [0002](0002-b.md) | B | Accepted |\n\nAfter the table.\n"
        )
        out = docs_adr.insert_index_row(text, "0003", "0003-c.md", "C")
        self.assertIn(
            "| [0002](0002-b.md) | B | Accepted |\n| [0003](0003-c.md) | C | Proposed |\n\nAfter the table.\n", out
        )
        self.assertEqual(docs_adr.index_format(text), "table")

    def test_list_row_is_appended(self):
        text = "# ADRs\n\n- [0001](0001-a.md) A\n- [0002](0002-b.md) B\n\nNotes.\n"
        out = docs_adr.insert_index_row(text, "0003", "0003-c.md", "C")
        self.assertIn("- [0002](0002-b.md) B\n- [0003](0003-c.md) C\n\nNotes.\n", out)
        self.assertEqual(docs_adr.index_format(text), "list")

    def test_header_only_table(self):
        text = "| ADR | Decision | Status |\n|---|---|---|\n"
        out = docs_adr.insert_index_row(text, "0001", "0001-a.md", "A")
        self.assertEqual(out, text + "| [0001](0001-a.md) | A | Proposed |\n")

    def test_two_and_four_column_tables(self):
        two = "| [0001](0001-a.md) | A |\n"
        self.assertEqual(
            docs_adr.insert_index_row(two, "0002", "0002-b.md", "B"), two + "| [0002](0002-b.md) | B |\n"
        )
        four = "| [0001](0001-a.md) | A | Accepted | 2026-01-01 |\n"
        self.assertEqual(
            docs_adr.insert_index_row(four, "0002", "0002-b.md", "B"),
            four + "| [0002](0002-b.md) | B | Proposed |  |\n",
        )

    def test_crlf_is_kept(self):
        text = "| [0001](0001-a.md) | A |\r\n| [0002](0002-b.md) | B |\r\n"
        out = docs_adr.insert_index_row(text, "0003", "0003-c.md", "C")
        self.assertEqual(out, text + "| [0003](0003-c.md) | C |\r\n")

    def test_prose_index_is_refused(self):
        text = "# Decisions\n\nWe write them down somewhere.\n"
        self.assertIsNone(docs_adr.index_format(text))
        with self.assertRaises(docs_adr.IndexFormatError):
            docs_adr.insert_index_row(text, "0001", "0001-a.md", "A")

    def test_index_targets(self):
        text = "- [0001](0001-a.md) A\n| [0002](<0002-b.md>) | B |\n[x](other.md)\n"
        self.assertEqual(docs_adr.index_targets(text), [(1, "0001-a.md"), (2, "0002-b.md")])

    def test_unrecognised_adrs(self):
        names = ["ADR-0001-x.md", "0002_Title.md", "0003-ok.md", "README.md"]
        self.assertEqual(docs_adr.unrecognised_adrs(names), ["ADR-0001-x.md", "0002_Title.md"])

    def test_status_and_date(self):
        self.assertEqual(
            docs_adr.status_of("# T\n\n- **Status:** Superseded by [0007](0007-x.md)\n"),
            (3, "Superseded by [0007](0007-x.md)"),
        )
        self.assertEqual(docs_adr.status_of("Status: Accepted\n"), (1, "Accepted"))
        self.assertEqual(docs_adr.date_of("# T\n- **Date:** 2026-01-02\n"), (2, "2026-01-02"))
        short = "# T\n- **Status:** Proposed · **Date:** 2026-01-02\n"
        self.assertEqual(docs_adr.status_of(short), (2, "Proposed"))
        self.assertEqual(docs_adr.date_of(short), (2, "2026-01-02"))
        self.assertIsNone(docs_adr.status_of("nothing\n"))

    def test_render_project_template(self):
        template = "# Title here\n\nStatus: accepted | proposed\nDate: YYYY-MM-DD\n\n## Why\n"
        out = docs_adr.render(template, "0004", "Pick a queue", "2026-11-25", True)
        self.assertTrue(out.startswith("# 0004. Pick a queue\n"))
        self.assertIn("Status: Proposed\n", out)
        self.assertIn("Date: 2026-11-25\n", out)
        self.assertIn("## Why", out)
        plain = docs_adr.render(template, "0004", "Pick a queue", "2026-11-25", False)
        self.assertTrue(plain.startswith("# Pick a queue\n"))

    def test_project_template_lookup(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            self.assertIsNone(docs_adr.project_template(d))
            (d / "template.md").write_text("x", encoding="utf-8")
            self.assertEqual(docs_adr.project_template(d), d / "template.md")
            (d / "0000-template.md").write_text("x", encoding="utf-8")
            self.assertEqual(docs_adr.project_template(d), d / "0000-template.md")


if __name__ == "__main__":
    unittest.main()
