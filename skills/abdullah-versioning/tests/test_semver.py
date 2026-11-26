import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from ver_semver import Version, bump, from_pep440, next_pre, to_pep440  # noqa: E402

V = Version.parse


class SemverTests(unittest.TestCase):
    def test_parse_and_format_round_trip(self):
        for text in ("1.2.3", "0.2.0-rc.1", "0.5.0-dev", "1.0.0-alpha.10"):
            with self.subTest(text=text):
                self.assertEqual(str(V(text)), text)
        for bad in ("1.2", "v1.2.3", "01.2.3", "1.2.3-", "1.2.3-rc.01", ""):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    V(bad)

    def test_precedence(self):
        texts = ["0.2.0", "0.2.0-rc.2", "0.2.0-alpha.1", "0.2.0-beta.1", "0.2.0-rc.1", "0.2.0-alpha.2", "0.1.9"]
        ordered = [str(v) for v in sorted(V(t) for t in texts)]
        self.assertEqual(ordered, ["0.1.9", "0.2.0-alpha.1", "0.2.0-alpha.2", "0.2.0-beta.1",
                                   "0.2.0-rc.1", "0.2.0-rc.2", "0.2.0"])
        self.assertGreater(V("1.0.0-alpha.10"), V("1.0.0-alpha.2"))
        self.assertGreater(V("0.5.0-dev"), V("0.5.0-beta.1"))
        self.assertEqual(V("1.2.3"), V("1.2.3"))

    def test_properties(self):
        self.assertTrue(V("1.2.3").is_final)
        self.assertFalse(V("1.2.3-rc.1").is_final)
        self.assertEqual(V("1.2.3-rc.1").stage, "rc")
        self.assertEqual(V("1.2.3-dev").stage, "dev")
        self.assertIsNone(V("1.2.3").stage)
        self.assertEqual(V("1.2.3-rc.1").final, V("1.2.3"))

    def test_bump(self):
        self.assertEqual(bump(V("0.3.0"), "minor"), V("0.4.0"))
        self.assertEqual(bump(V("0.3.0"), "patch"), V("0.3.1"))
        self.assertEqual(bump(V("1.4.2"), "major"), V("2.0.0"))
        self.assertEqual(bump(V("0.4.0-dev"), "minor"), V("0.5.0"))
        with self.assertRaises(ValueError):
            bump(V("1.0.0"), "huge")

    def test_next_pre(self):
        target = V("0.2.0")
        self.assertEqual(next_pre(target, "rc", []), V("0.2.0-rc.1"))
        self.assertEqual(next_pre(target, "rc", [V("0.2.0-rc.1")]), V("0.2.0-rc.2"))
        self.assertEqual(next_pre(target, "rc", [V("0.2.0-beta.3")]), V("0.2.0-rc.1"))
        with self.assertRaises(ValueError):
            next_pre(target, "beta", [V("0.2.0-rc.1")])
        self.assertEqual(next_pre(target, "rc", [V("0.1.0-rc.4"), V("0.3.0-rc.2")]), V("0.2.0-rc.1"))

    def test_pep440(self):
        pairs = [("0.2.0-rc.1", "0.2.0rc1"), ("0.2.0-alpha.1", "0.2.0a1"), ("0.2.0-beta.2", "0.2.0b2"),
                 ("0.5.0-dev", "0.5.0.dev0"), ("1.0.0", "1.0.0")]
        for semver, pep in pairs:
            with self.subTest(semver=semver):
                self.assertEqual(to_pep440(V(semver)), pep)
                self.assertEqual(from_pep440(pep), V(semver))
        self.assertEqual(from_pep440("0.2.0-rc.1"), V("0.2.0-rc.1"))
        self.assertEqual(from_pep440("0.2.0rc.1"), V("0.2.0-rc.1"))
        with self.assertRaises(ValueError):
            from_pep440("not a version")


if __name__ == "__main__":
    unittest.main()
