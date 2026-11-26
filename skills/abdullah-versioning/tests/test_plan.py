import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from ver_plan import propose  # noqa: E402
from ver_semver import Version  # noqa: E402

V = Version.parse
FIRST = V("0.1.0")


class PlanTests(unittest.TestCase):
    def test_first_release(self):
        p = propose(None, {"Added": ["- Workspace export."]}, first=FIRST)
        self.assertEqual((p.next, p.part, p.current), (V("0.1.0"), "first", None))
        p = propose(None, {"Added": ["- Workspace export."]}, first=FIRST, pre="rc")
        self.assertEqual(p.next, V("0.1.0-rc.1"))
        self.assertEqual(p.pre, "rc")

    def test_before_1_0(self):
        cur = V("0.3.0")
        p = propose(cur, {"Added": ["- workspace export"]}, first=FIRST)
        self.assertEqual((p.next, p.part), (V("0.4.0"), "minor"))
        self.assertEqual(p.reasons, ["Added: workspace export"])
        self.assertEqual(propose(cur, {"Fixed": ["- b"]}, first=FIRST).next, V("0.3.1"))
        self.assertEqual(propose(cur, {"Removed": ["- c"]}, first=FIRST).next, V("0.4.0"))
        self.assertEqual(propose(cur, {"Fixed": ["- b"]}, first=FIRST, major=True).next, V("0.4.0"))

    def test_from_1_0(self):
        cur = V("1.4.2")
        self.assertEqual(propose(cur, {"Removed": ["- c"]}, first=FIRST).next, V("2.0.0"))
        p = propose(cur, {"Changed": ["- the export format\n  is now CSV"]}, first=FIRST)
        self.assertEqual((p.next, p.part), (V("1.5.0"), "minor"))
        self.assertEqual(p.judgment, ["Changed: the export format"])
        self.assertEqual(propose(cur, {"Changed": ["- d"]}, first=FIRST, major=True).next, V("2.0.0"))
        self.assertEqual(propose(cur, {"Security": ["- e"]}, first=FIRST).next, V("1.4.3"))

    def test_unknown_subsection_needs_judgment(self):
        p = propose(V("1.0.0"), {"Performance": ["- faster"]}, first=FIRST)
        self.assertEqual(p.next, V("1.1.0"))
        self.assertEqual(p.judgment, ["Performance: faster"])

    def test_long_entries_are_shortened_in_reasons(self):
        long = "- `Kernel`: the seams the agent resolves and writes through. " + "More detail. " * 30
        p = propose(V("0.6.0"), {"Added": [long]}, first=FIRST)
        self.assertEqual(p.reasons, ["Added: `Kernel`: the seams the agent resolves and writes through."])
        p = propose(V("0.6.0"), {"Added": ["- " + "x" * 300]}, first=FIRST)
        self.assertLessEqual(len(p.reasons[0]), len("Added: ") + 120)
        self.assertTrue(p.reasons[0].endswith("…"))

    def test_pre_release_numbering(self):
        p = propose(V("0.3.0"), {"Added": ["- a"]}, first=FIRST, pre="rc", existing=[V("0.4.0-rc.1")])
        self.assertEqual(p.next, V("0.4.0-rc.2"))

    def test_empty_is_refused(self):
        with self.assertRaises(ValueError) as cm:
            propose(V("0.3.0"), {}, first=FIRST)
        self.assertEqual(str(cm.exception), "[Unreleased] has no entries to release")
        with self.assertRaises(ValueError):
            propose(V("0.3.0"), {"Added": []}, first=FIRST)


if __name__ == "__main__":
    unittest.main()
