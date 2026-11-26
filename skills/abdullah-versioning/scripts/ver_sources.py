"""Read and write the places a project declares its version.

Each writer replaces only the version text: every other byte of the file, its BOM and
its line endings stay as they were.
"""
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ver_semver import Version, from_pep440, to_pep440

SKIP_DIRS = {".git", "node_modules", "bin", "obj", "target", ".venv", "venv", "dist", "build", "__pycache__"}
MAX_DEPTH = 3
_PY_VERSION_FILES = {"__init__.py", "_version.py", "__about__.py", "version.py"}
_MSBUILD_EXT = (".csproj", ".fsproj", ".vbproj")

_MS_VERSION = re.compile(r"<Version>([^<]*)</Version>")
_MS_PREFIX = re.compile(r"<VersionPrefix>([^<]*)</VersionPrefix>")
_MS_SUFFIX = re.compile(r"<VersionSuffix>([^<]*)</VersionSuffix>|<VersionSuffix\s*/>")
_PY_VERSION = re.compile(r"""^__version__[ \t]*(?::[ \t]*str[ \t]*)?=[ \t]*(["'])([^"'\n]*)\1""", re.M)
_TOML_HEADER = re.compile(r"^[ \t]*\[([^\[\]\r\n]+)\][ \t]*(?:#[^\r\n]*)?\r?$")
_TOML_ARRAY_HEADER = re.compile(r"^[ \t]*\[\[([^\[\]\r\n]+)\]\][ \t]*(?:#[^\r\n]*)?\r?$")
_TOML_KEY = r"^[ \t]*{key}[ \t]*=[ \t]*([\"'])([^\"'\n]*)\1"
_TOML_DYNAMIC = re.compile(r"""^[ \t]*dynamic[ \t]*=[ \t]*\[[^\]]*["']version["']""", re.M)


@dataclass(frozen=True)
class Source:
    spec: str
    path: str
    kind: str
    pattern: Optional[str] = None


def _inside(path: str, spec: str) -> str:
    """A source path must be relative and stay inside the repository."""
    path = path.replace("\\", "/")
    if path.startswith("/") or re.match(r"^[A-Za-z]:", path) or ".." in path.split("/"):
        raise ValueError(f"source {spec!r} is outside the repository: use a path relative to its root")
    return path


def parse_source(spec: str) -> Source:
    spec = spec.strip()
    if spec == "tag":
        return Source(spec, "", "tag")
    if "#" in spec:
        path, _, pattern = spec.partition("#")
        return Source(spec, _inside(path, spec), "regex", pattern)
    path = _inside(spec, spec)
    name = path.rsplit("/", 1)[-1]
    if name == "Directory.Build.props" or name.endswith(_MSBUILD_EXT):
        kind = "msbuild"
    elif name == "pyproject.toml":
        kind = "pyproject"
    elif name.endswith(".py"):
        kind = "python"
    elif name == "package.json":
        kind = "npm"
    elif name == "package-lock.json":
        kind = "npm-lock"
    elif name == "Cargo.toml":
        kind = "cargo"
    elif name == "Cargo.lock":
        kind = "cargo-lock"
    elif name.endswith(".json"):
        kind = "json"
    else:
        kind = "plain"
    return Source(spec, path, kind)


# --- file access -------------------------------------------------------------------

def _file(root: Path, src: Source) -> Path:
    """The source's file, refused when it resolves outside the repository (a link out of it)."""
    base = Path(root).resolve()
    path = (base / src.path).resolve()
    if path != base and base not in path.parents:
        raise ValueError(f"{src.path}: resolves outside the repository")
    return path


def _load(root: Path, src: Source):
    raw = _file(root, src).read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    return raw[3:].decode("utf-8", errors="surrogateescape") if bom else raw.decode("utf-8", errors="surrogateescape"), bom




# --- span finders: each returns a list of (start, end) spans of the version text -----

def _json_spans(text: str, path: list) -> list:
    """Spans of the string values at a key path, found by a small JSON scanner."""
    found = []
    n = len(text)

    def ws(i):
        while i < n and text[i] in " \t\r\n":
            i += 1
        return i

    def string_end(i):
        j = i + 1
        while text[j] != '"':
            j += 2 if text[j] == "\\" else 1
        return j + 1

    def value(i, cur):
        i = ws(i)
        c = text[i]
        if c == "{":
            i = ws(i + 1)
            if text[i] == "}":
                return i + 1
            while True:
                i = ws(i)
                key_end = string_end(i)
                key = json.loads(text[i:key_end])
                i = ws(key_end) + 1  # past ':'
                start = ws(i)
                end = value(start, cur + [key])
                if cur + [key] == path and text[start] == '"':
                    found.append((start + 1, end - 1))
                i = ws(end)
                if text[i] == ",":
                    i += 1
                    continue
                return i + 1  # past '}'
        if c == "[":
            i = ws(i + 1)
            if text[i] == "]":
                return i + 1
            index = 0
            while True:
                i = ws(value(i, cur + [index]))
                index += 1
                if text[i] == ",":
                    i += 1
                    continue
                return i + 1
        if c == '"':
            return string_end(i)
        while i < n and text[i] not in ",}] \t\r\n":
            i += 1
        return i

    try:
        json.loads(text)
        value(0, [])
    except (ValueError, IndexError):
        return []
    return found


def _toml_table_spans(text: str, tables: tuple, key: str = "version") -> list:
    key_re = re.compile(_TOML_KEY.format(key=key))
    current, offset = None, 0
    for line in text.splitlines(keepends=True):
        header = _TOML_HEADER.match(line)
        if header:
            current = header.group(1).strip()
        elif _TOML_ARRAY_HEADER.match(line):
            current = None
        elif current in tables:
            m = key_re.match(line)
            if m:
                return [(offset + m.start(2), offset + m.end(2))]
        offset += len(line)
    return []


def _cargo_lock_spans(text: str, package: str) -> list:
    blocks = re.split(r"(?m)^(?=\[\[package\]\])", text)
    offset = 0
    for block in blocks:
        name = re.search(r'(?m)^name[ \t]*=[ \t]*"([^"]*)"', block)
        version = re.search(r'(?m)^version[ \t]*=[ \t]*"([^"]*)"', block)
        if block.startswith("[[package]]") and name and version and name.group(1) == package:
            return [(offset + version.start(1), offset + version.end(1))]
        offset += len(block)
    return []


def _cargo_package_name(root: Path, src: Source) -> Optional[str]:
    toml = (Path(root) / src.path).parent / "Cargo.toml"
    if not toml.is_file():
        return None
    text = toml.read_bytes().decode("utf-8", errors="replace")
    spans = _toml_table_spans(text, ("package",), key="name")
    return text[spans[0][0]:spans[0][1]] if spans else None


def _spans(root: Path, src: Source, text: str) -> list:
    kind = src.kind
    if kind == "msbuild":
        m = _MS_VERSION.search(text)
        return [m.span(1)] if m else []
    if kind == "pyproject":
        return _toml_table_spans(text, ("project", "tool.poetry"))
    if kind == "python":
        m = _PY_VERSION.search(text)
        return [m.span(2)] if m else []
    if kind in ("npm", "json"):
        return _json_spans(text, ["version"])
    if kind == "npm-lock":
        return sorted(_json_spans(text, ["version"]) + _json_spans(text, ["packages", "", "version"]))
    if kind == "cargo":
        return _toml_table_spans(text, ("package",))
    if kind == "cargo-lock":
        name = _cargo_package_name(root, src)
        return _cargo_lock_spans(text, name) if name else []
    if kind == "plain":
        m = re.search(r"\S+", text)
        return [m.span()] if m else []
    if kind == "regex":
        m = re.compile(src.pattern, re.M).search(text)
        return [m.span(1)] if m and m.groups() else []
    return []


# --- public API --------------------------------------------------------------------

def _msbuild_prefix_raw(text: str) -> Optional[str]:
    prefix = _MS_PREFIX.search(text)
    if not prefix:
        return None
    suffix = _MS_SUFFIX.search(text)
    label = suffix.group(1) if suffix and suffix.group(1) else ""
    return f"{prefix.group(1)}-{label}" if label else prefix.group(1)


def read_raw(root: Path, src: Source) -> Optional[str]:
    if src.kind == "tag":
        return None
    try:
        text, _ = _load(root, src)
    except OSError:
        return None
    spans = _spans(root, src, text)
    if spans:
        return text[spans[0][0]:spans[0][1]]
    if src.kind == "msbuild":
        return _msbuild_prefix_raw(text)
    return None


def read_version(root: Path, src: Source) -> Version:
    raw = read_raw(root, src)
    if raw is None:
        raise ValueError(f"{src.path or src.spec}: no version found")
    try:
        return from_pep440(raw) if src.kind in ("pyproject", "python") else Version.parse(raw)
    except ValueError:
        raise ValueError(f"{src.path}: {raw!r} is not a semantic version") from None


def _form(src: Source, v: Version) -> str:
    return to_pep440(v) if src.kind in ("pyproject", "python") else str(v)


def render_version(root: Path, src: Source, v: Version) -> bytes:
    """The source file's bytes with v declared; nothing is written. Raises ValueError."""
    text, bom = _load(root, src)
    spans = _spans(root, src, text)
    if not spans and src.kind == "msbuild" and _MS_PREFIX.search(text):
        text = _write_prefix_suffix(text, v)
    elif not spans:
        raise ValueError(f"{src.path}: no version found")
    else:
        new = _form(src, v)
        for start, end in sorted(spans, reverse=True):
            text = text[:start] + new + text[end:]
    return (b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8", errors="surrogateescape")


def write_version(root: Path, src: Source, v: Version) -> None:
    if src.kind == "tag":
        return
    _file(root, src).write_bytes(render_version(root, src, v))


def _write_prefix_suffix(text: str, v: Version) -> str:
    label = ".".join(str(p) for p in v.pre)
    suffix = _MS_SUFFIX.search(text)
    if suffix:
        if suffix.group(1) is not None:
            text = text[:suffix.start(1)] + label + text[suffix.end(1):]
        elif label:
            text = text[:suffix.start()] + f"<VersionSuffix>{label}</VersionSuffix>" + text[suffix.end():]
    elif label:
        close = _MS_PREFIX.search(text).end()
        text = text[:close] + f"<VersionSuffix>{label}</VersionSuffix>" + text[close:]
    prefix = _MS_PREFIX.search(text)
    core = str(v.final)
    return text[:prefix.start(1)] + core + text[prefix.end(1):]


def _has_version(root: Path, src: Source) -> bool:
    try:
        read_version(root, src)
        return True
    except (ValueError, OSError):
        return False


def _walk(root: Path):
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = Path(dirpath).relative_to(root)
        depth = len(rel_dir.parts)
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and depth < MAX_DEPTH)
        for name in sorted(filenames):
            yield (rel_dir / name).as_posix(), name


def discover(root: Path) -> list:
    root = Path(root)
    found, tag = [], False
    for rel, name in _walk(root):
        if name == "pyproject.toml":
            text = (root / rel).read_bytes().decode("utf-8", errors="replace")
            if _TOML_DYNAMIC.search(text):
                tag = True
                continue
        if name in _PY_VERSION_FILES or name == "Directory.Build.props" or name.endswith(_MSBUILD_EXT) or name in (
                "pyproject.toml", "package.json", "package-lock.json", "Cargo.toml", "Cargo.lock", "VERSION") or (
                rel == ".claude-plugin/plugin.json"):
            src = parse_source(rel)
            if _has_version(root, src):
                found.append(src)
    if tag:
        found.append(Source("tag", "", "tag"))
    return sorted(found, key=lambda s: s.spec)


def assembly_info(root: Path) -> list:
    root = Path(root)
    hits = []
    for rel, name in _walk(root):
        if name == "AssemblyInfo.cs" and "AssemblyVersion" in (root / rel).read_bytes().decode("utf-8", errors="replace"):
            hits.append(rel)
    return hits
