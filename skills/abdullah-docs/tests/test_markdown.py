import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from docs_markdown import Link, code_paths, heading_slugs, is_repo_path, links, split_lines


class LinkTests(unittest.TestCase):
    def test_basic_and_urls(self):
        self.assertEqual(
            links("See [x](docs/a.md#part) and [y](https://e.com) [z](mailto:a@b.c)."),
            [Link(1, "docs/a.md", "part")],
        )

    def test_syntax_variants(self):
        for src, want in [
            ("[a](<docs/my file.md>)", "docs/my file.md"),
            ('[a](docs/x.md "T")', "docs/x.md"),
            ("[a](docs/my%20file.md)", "docs/my file.md"),
        ]:
            self.assertEqual(links(src), [Link(1, want, None)], src)

    def test_reference_definition(self):
        self.assertEqual(links("[a]: docs/x.md"), [Link(1, "docs/x.md", None)])

    def test_same_file_anchor(self):
        self.assertEqual(links("[a](#intro)"), [Link(1, "", "intro")])

    def test_code_ignored(self):
        text = "```\n[a](b.md)\n```\nx `[a](b.md)` y\n[c](d.md)\n"
        self.assertEqual(links(text), [Link(5, "d.md", None)])

    def test_footnote_is_not_a_reference(self):
        self.assertEqual(links("[^1]: See the design notes."), [])

    def test_inline_triple_backticks_do_not_open_a_fence(self):
        text = "```js``` then [a](b.md)\n[c](d.md)\n# Head\n"
        self.assertEqual(links(text), [Link(1, "b.md", None), Link(2, "d.md", None)])
        self.assertEqual(heading_slugs(text), {"head"})

    def test_crlf(self):
        text = "a\n\n[x](a.md#h)\n```\n[y](b.md)\n```\n[z]: c.md\n"
        self.assertEqual(links(text.replace("\n", "\r\n")), links(text))
        self.assertEqual(links(text), [Link(3, "a.md", "h"), Link(7, "c.md", None)])

    def test_split_lines(self):
        self.assertEqual(split_lines("a\r\nb\nc"), ["a", "b", "c"])


class CodePathTests(unittest.TestCase):
    def test_code_paths(self):
        text = "Run `src/app/main.py` and `npm test`, see `docs/<name>.md` and `~/x/y.md`."
        self.assertEqual(code_paths(text), [(1, "src/app/main.py")])

    def test_fence_skipped(self):
        self.assertEqual(code_paths("```\n`a/b.py`\n```\n`c/d.py`"), [(4, "c/d.py")])

    def test_is_repo_path(self):
        for ok in ["a/b.py", ".github/workflows/check.yml"]:
            self.assertTrue(is_repo_path(ok), ok)
        for bad in ["https://a/b.md", "a/*.md", "docs/<x>.md", "/abs/p.md",
                    "C:/x/y.md", "~/a/b.md", "nofolder.md", "a/b"]:
            self.assertFalse(is_repo_path(bad), bad)

    def test_variables_options_and_hosts_are_not_paths(self):
        for bad in ["$HOME/.config/foo.toml", "{project}/README.md", "%APPDATA%/x/y.json",
                    "github.com/owner/repo.git", "user@host:dir/x.sh", "--out=dist/x.json", "key=a/b.c"]:
            self.assertFalse(is_repo_path(bad), bad)
        for ok in ["Acme.Api/Hosting/WebApp.cs", ".github/workflows/check.yml", ".agents/adr/README.md"]:
            self.assertTrue(is_repo_path(ok), ok)


class SlugTests(unittest.TestCase):
    def test_slugs(self):
        self.assertEqual(
            heading_slugs("# Hello World!\n## Hello World"), {"hello-world", "hello-world-1"}
        )

    def test_fence_ignored(self):
        self.assertEqual(heading_slugs("```\n# nope\n```\n# Yes"), {"yes"})


if __name__ == "__main__":
    unittest.main()
