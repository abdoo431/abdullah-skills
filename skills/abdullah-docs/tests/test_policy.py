import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import tempfile

from docs_policy import AGENT_SECTION_HEADING, Settings, find_policy, read_settings

BLOCK = """# Policy

Documentation profile: full

```abdullah-docs
adr-dir: .agents/adr
base: origin/main
history: docs/plans/**, conversations/**
pairs: specs/*-design.md:specs/*-design.en.md
unknown-key: ignored
```
"""


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def test_block(self):
        s = read_settings(self.write("DOCUMENTATION.md", BLOCK))
        self.assertEqual(s.profile, "full")
        self.assertEqual(s.adr_dir, ".agents/adr")
        self.assertEqual(s.base, "origin/main")
        self.assertEqual(s.history, ["docs/plans/**", "conversations/**"])
        self.assertEqual(s.pairs, [("specs/*-design.md", "specs/*-design.en.md")])
        self.assertEqual(s.changelog, "CHANGELOG.md")

    def test_none_gives_defaults(self):
        self.assertEqual(read_settings(None), Settings())
        s = Settings()
        self.assertEqual((s.profile, s.adr_dir, s.base), ("lean", "docs/adr", None))
        self.assertEqual(s.specs, "docs/superpowers/specs")
        self.assertEqual(s.plans, "docs/superpowers/plans")

    def test_defaults_not_shared(self):
        a, b = Settings(), Settings()
        a.history.append("x")
        self.assertEqual(b.history, [])

    def test_profile_without_block(self):
        s = read_settings(self.write("DOCUMENTATION.md", "Documentation profile: full\n"))
        self.assertEqual(s.profile, "full")
        self.assertEqual(s.adr_dir, "docs/adr")

    def test_profile_normalised(self):
        for line, want in [("Documentation profile: `full`", "full"),
                           ("Documentation profile: Full.", "full"),
                           ("Documentation profile:\nlean text", "lean")]:
            s = read_settings(self.write("DOCUMENTATION.md", line + "\n"))
            self.assertEqual(s.profile, want, line)

    def test_specs_plans_changelog(self):
        text = "```abdullah-docs\nspecs: docs/design\nplans: docs/plans\nchangelog: HISTORY.md\n```\n"
        s = read_settings(self.write("DOCUMENTATION.md", text))
        self.assertEqual((s.specs, s.plans, s.changelog), ("docs/design", "docs/plans", "HISTORY.md"))

    def test_examples(self):
        text = "```abdullah-docs\nexamples: skills/**, README.md\n```\n"
        s = read_settings(self.write("DOCUMENTATION.md", text))
        self.assertEqual(s.examples, ["skills/**", "README.md"])

    def test_find_policy(self):
        self.assertIsNone(find_policy(self.root))
        self.write("CONTRIBUTING.md", "# Contributing\n")
        self.assertIsNone(find_policy(self.root))
        self.write("CONTRIBUTING.md", "# Contributing\n\n## Documentation\n")
        self.assertEqual(find_policy(self.root), self.root / "CONTRIBUTING.md")
        self.write("DOCUMENTATION.md", "x")
        self.assertEqual(find_policy(self.root), self.root / "DOCUMENTATION.md")
        self.write("docs/DOCUMENTATION.md", "x")
        self.assertEqual(find_policy(self.root), self.root / "docs" / "DOCUMENTATION.md")

    def test_heading_constant(self):
        self.assertEqual(AGENT_SECTION_HEADING, "## Documentation (abdullah-docs)")


if __name__ == "__main__":
    unittest.main()
