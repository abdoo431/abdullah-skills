import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import ver_sources as vs  # noqa: E402
from ver_semver import Version  # noqa: E402

V = Version.parse
BOM = b"\xef\xbb\xbf"

FILES = {
    "Directory.Build.props": BOM + b"<Project>\r\n  <PropertyGroup>\r\n    <Version>0.1.0</Version>\r\n"
                             b"  </PropertyGroup>\r\n</Project>\r\n",
    "pyproject.toml": b'[project]\nname = "x"\nversion="0.1.0"\n\n[tool.other]\nversion = "9.9.9"\n',
    "app/__init__.py": b"__version__ = '0.1.0'\n",
    "package.json": b'{\n\t"name": "web",\n\t"version": "0.1.0",\n\t"dependencies": {\n\t\t"some-lib": "0.1.0"\n\t}\n}\n',
    "Cargo.toml": b'[package]\nname = "app"\nversion = "0.1.0"\n\n[dependencies]\nserde = { version = "0.1.0" }\n',
    ".claude-plugin/plugin.json": b'{\n  "name": "p",\n  "version": "0.1.0"\n}\n',
    "VERSION": b"0.1.0\n",
    "src/app.go": b'package app\n\nconst Version = "0.1.0"\n',
}
SPECS = {
    "Directory.Build.props": ("Directory.Build.props", "msbuild"),
    "pyproject.toml": ("pyproject.toml", "pyproject"),
    "app/__init__.py": ("app/__init__.py", "python"),
    "package.json": ("package.json", "npm"),
    "Cargo.toml": ("Cargo.toml", "cargo"),
    ".claude-plugin/plugin.json": (".claude-plugin/plugin.json", "json"),
    "VERSION": ("VERSION", "plain"),
    "src/app.go": ('src/app.go#const Version = "(.*)"', "regex"),
}
# The exact text each writer must produce for 0.2.0-rc.1, replacing the old text once.
WRITTEN = {
    "Directory.Build.props": (b"<Version>0.1.0</Version>", b"<Version>0.2.0-rc.1</Version>"),
    "pyproject.toml": (b'version="0.1.0"', b'version="0.2.0rc1"'),
    "app/__init__.py": (b"'0.1.0'", b"'0.2.0rc1'"),
    "package.json": (b'"version": "0.1.0"', b'"version": "0.2.0-rc.1"'),
    "Cargo.toml": (b'version = "0.1.0"', b'version = "0.2.0-rc.1"'),
    ".claude-plugin/plugin.json": (b'"version": "0.1.0"', b'"version": "0.2.0-rc.1"'),
    "VERSION": (b"0.1.0", b"0.2.0-rc.1"),
    "src/app.go": (b'"0.1.0"', b'"0.2.0-rc.1"'),
}

LOCK = b"""{
  "name": "web",
  "version": "0.1.0",
  "lockfileVersion": 3,
  "requires": true,
  "packages": {
    "node_modules/some-lib": {
      "version": "0.1.0",
      "resolved": "x"
    },
    "": {
      "name": "web",
      "version": "0.1.0",
      "dependencies": {
        "some-lib": "0.1.0"
      }
    }
  }
}
"""
CARGO_LOCK = b'version = 3\n\n[[package]]\nname = "serde"\nversion = "0.1.0"\n\n[[package]]\nname = "app"\nversion = "0.1.0"\n'


class SourcesTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _put(self, rel: str, data: bytes) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def test_parse_source_kinds(self):
        for rel, (spec, kind) in SPECS.items():
            with self.subTest(spec=spec):
                src = vs.parse_source(spec)
                self.assertEqual((src.path, src.kind), (rel, kind))
        self.assertEqual(vs.parse_source("src/web/package-lock.json").kind, "npm-lock")
        self.assertEqual(vs.parse_source("Cargo.lock").kind, "cargo-lock")
        self.assertEqual(vs.parse_source("src/App/App.csproj").kind, "msbuild")
        self.assertEqual(vs.parse_source("tag").kind, "tag")
        regex = vs.parse_source(SPECS["src/app.go"][0])
        self.assertEqual(regex.pattern, 'const Version = "(.*)"')

    def test_read_each_kind(self):
        FILES_RC = dict(FILES, **{"app/__init__.py": b"__version__ = '0.2.0rc1'\n"})
        for rel, data in FILES_RC.items():
            self._put(rel, data)
        for rel, (spec, _) in SPECS.items():
            with self.subTest(spec=spec):
                expected = V("0.2.0-rc.1") if rel == "app/__init__.py" else V("0.1.0")
                self.assertEqual(vs.read_version(self.root, vs.parse_source(spec)), expected)
        self.assertEqual(vs.read_raw(self.root, vs.parse_source("app/__init__.py")), "0.2.0rc1")

    def test_write_keeps_every_other_byte(self):
        for rel, data in FILES.items():
            self._put(rel, data)
        for rel, (spec, _) in SPECS.items():
            with self.subTest(spec=spec):
                vs.write_version(self.root, vs.parse_source(spec), V("0.2.0-rc.1"))
                old, new = WRITTEN[rel]
                self.assertEqual((self.root / rel).read_bytes(), FILES[rel].replace(old, new, 1))

    def test_lock_file_changes_root_entries_only(self):
        self._put("package-lock.json", LOCK)
        vs.write_version(self.root, vs.parse_source("package-lock.json"), V("0.2.0"))
        out = (self.root / "package-lock.json").read_bytes()
        expected = LOCK.replace(b'"web",\n  "version": "0.1.0"', b'"web",\n  "version": "0.2.0"')
        expected = expected.replace(b'"name": "web",\n      "version": "0.1.0"', b'"name": "web",\n      "version": "0.2.0"')
        self.assertEqual(out, expected)
        self.assertIn(b'"node_modules/some-lib": {\n      "version": "0.1.0"', out)

        self._put("Cargo.toml", FILES["Cargo.toml"])
        self._put("Cargo.lock", CARGO_LOCK)
        vs.write_version(self.root, vs.parse_source("Cargo.lock"), V("0.2.0"))
        self.assertEqual((self.root / "Cargo.lock").read_bytes(),
                         CARGO_LOCK.replace(b'name = "app"\nversion = "0.1.0"', b'name = "app"\nversion = "0.2.0"'))

    def test_version_prefix_and_suffix(self):
        props = b"<Project><PropertyGroup><VersionPrefix>0.1.0</VersionPrefix><VersionSuffix></VersionSuffix></PropertyGroup></Project>"
        self._put("Directory.Build.props", props)
        src = vs.parse_source("Directory.Build.props")
        self.assertEqual(vs.read_version(self.root, src), V("0.1.0"))
        vs.write_version(self.root, src, V("0.2.0-rc.1"))
        self.assertIn(b"<VersionPrefix>0.2.0</VersionPrefix><VersionSuffix>rc.1</VersionSuffix>",
                      (self.root / "Directory.Build.props").read_bytes())
        self.assertEqual(vs.read_version(self.root, src), V("0.2.0-rc.1"))
        vs.write_version(self.root, src, V("0.2.0"))
        self.assertIn(b"<VersionPrefix>0.2.0</VersionPrefix><VersionSuffix></VersionSuffix>",
                      (self.root / "Directory.Build.props").read_bytes())

    def test_discover(self):
        self._put("Directory.Build.props", FILES["Directory.Build.props"])
        self._put("src/web/package.json", FILES["package.json"])
        self._put("src/web/package-lock.json", LOCK)
        self._put("node_modules/x/package.json", FILES["package.json"])
        self._put("src/App/App.csproj", b"<Project><PropertyGroup><TargetFramework>net9.0</TargetFramework></PropertyGroup></Project>")
        found = [s.spec for s in vs.discover(self.root)]
        self.assertEqual(found, ["Directory.Build.props", "src/web/package-lock.json", "src/web/package.json"])

    def test_discover_dynamic_pyproject_gives_tag(self):
        self._put("pyproject.toml", b'[project]\nname = "x"\ndynamic = ["version"]\n')
        self.assertEqual([(s.spec, s.kind) for s in vs.discover(self.root)], [("tag", "tag")])

    def test_assembly_info(self):
        self._put("src/App/Properties/AssemblyInfo.cs", b'[assembly: AssemblyVersion("1.0.0.0")]\n')
        self.assertEqual(vs.assembly_info(self.root), ["src/App/Properties/AssemblyInfo.cs"])

    def test_source_paths_stay_inside_the_repository(self):
        for spec in ("../x/package.json", "/etc/VERSION", "C:/x/VERSION", "a/../../VERSION", "../a.go#v = (.*)"):
            with self.subTest(spec=spec):
                with self.assertRaises(ValueError):
                    vs.parse_source(spec)

    def test_write_refuses_a_link_out_of_the_repository(self):
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "VERSION"
            target.write_bytes(b"0.1.0\n")
            try:
                (self.root / "VERSION").symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are not available")
            with self.assertRaises(ValueError):
                vs.write_version(self.root, vs.parse_source("VERSION"), V("0.2.0"))
            self.assertEqual(target.read_bytes(), b"0.1.0\n")

    def test_unreadable_source(self):
        self._put("package.json", b'{"name": "web"}\n')
        with self.assertRaises(ValueError) as cm:
            vs.read_version(self.root, vs.parse_source("package.json"))
        self.assertIn("package.json", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
