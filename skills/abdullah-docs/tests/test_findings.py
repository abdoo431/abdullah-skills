import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from docs_findings import error, exit_code, format_finding, warning


class FindingTests(unittest.TestCase):
    def test_format(self):
        f = error("a/b.md", 3, "adr-index", "missing row")
        self.assertEqual(format_finding(f), "a/b.md:3: error: adr-index: missing row")

    def test_exit_codes(self):
        self.assertEqual(exit_code([]), 0)
        self.assertEqual(exit_code([warning("a", 1, "k", "m")]), 0)
        self.assertEqual(
            exit_code([warning("a", 1, "k", "m"), error("a", 1, "k", "m")]), 1
        )


if __name__ == "__main__":
    unittest.main()
