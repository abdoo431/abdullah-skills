"""Survey a project's versions for the setup, and report its release status."""
import fnmatch
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

import ver_changelog
import ver_git
import ver_sources
from ver_findings import error, format_finding, warning
from ver_policy import Settings
from ver_semver import Version, from_pep440

ROLE_NAMES = {
    "production": ("main", "master", "production", "release", "trunk"),
    "staging": ("staging", "stage", "uat", "preprod"),
    "integration": ("dev", "develop", "development"),
}
SUPPORT_PATTERNS = ("support/*", "maintenance/*", "release/*.x")
_TAG_RE = re.compile(r"^(?P<prefix>.*?)(?P<v>\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)$")
_VERSION_LIKE_RE = re.compile(r"^[A-Za-z_-]*\d+(?:\.\d+)+")
_NO_GIT = "not a git repository: tags and branches were not read"


@dataclass
class Survey:
    git: bool
    tags: list = field(default_factory=list)
    tag_format: Optional[str] = None
    stray_tags: list = field(default_factory=list)
    non_semver: bool = False
    sources: list = field(default_factory=list)
    changelog: Optional[str] = None
    has_unreleased: bool = False
    released: list = field(default_factory=list)
    roles: dict = field(default_factory=dict)
    support: list = field(default_factory=list)
    layout: Optional[str] = None
    verdict: str = "new"
    current: Optional[str] = None
    stops: list = field(default_factory=list)
    assembly_info: list = field(default_factory=list)
    findings: list = field(default_factory=list)

    def to_json(self) -> str:
        data = asdict(self)
        data["findings"] = [format_finding(f) for f in self.findings]
        data["sources"] = [{"spec": spec, "version": raw} for spec, raw in self.sources]
        return json.dumps(data, indent=2)


@dataclass
class Status:
    layout: Optional[str]
    branch: Optional[str]
    role: Optional[str]
    latest: Optional[Version]
    declared: dict
    changelog_latest: Optional[str]
    agree: bool
    due: Optional[str]
    findings: list = field(default_factory=list)


def parse_declared(spec: str, raw: Optional[str]) -> Optional[Version]:
    if raw is None:
        return None
    try:
        kind = ver_sources.parse_source(spec).kind
        return from_pep440(raw) if kind in ("pyproject", "python") else Version.parse(raw)
    except ValueError:
        return None


def _tag_scan(root: Path):
    """(version tags, tag format, stray tags, non-SemVer version-like tags exist)."""
    by_prefix, stray, version_like = {}, [], False
    for tag in ver_git.all_tags(root):
        m = _TAG_RE.match(tag)
        parsed = None
        if m:
            try:
                parsed = Version.parse(m.group("v"))
            except ValueError:
                parsed = None
        if parsed is None:
            if _VERSION_LIKE_RE.match(tag):
                version_like = True
            else:
                stray.append(tag)
            continue
        by_prefix.setdefault(m.group("prefix"), []).append((tag, parsed))
    if not by_prefix:
        return [], None, sorted(stray), version_like
    prefix = Counter({p: len(t) for p, t in by_prefix.items()}).most_common(1)[0][0]
    for other, tags in by_prefix.items():
        if other != prefix:
            stray += [t for t, _ in tags]
    tags = [t for t, _ in sorted(by_prefix[prefix], key=lambda tv: tv[1])]
    return tags, prefix + "{version}", sorted(stray), False


def _roles(root: Path, names: list, latest_tag: Optional[str]) -> dict:
    roles = {role: next((n for n in candidates if n in names), None) for role, candidates in ROLE_NAMES.items()}
    if latest_tag:
        containing = ver_git.branches_containing(root, latest_tag)
        prod = next((n for n in ROLE_NAMES["production"] if n in containing), None)
        if prod:
            roles["production"] = prod
    return roles


def _layout(roles: dict) -> Optional[str]:
    if roles["integration"] and roles["staging"]:
        return "dev-staging-main"
    if roles["integration"]:
        return "dev-main"
    if roles["staging"]:
        return None
    return "main"


def _changelog_path(root: Path, name: str = "CHANGELOG.md") -> Optional[Path]:
    path = Path(root) / name
    return path if path.is_file() else None


def survey(root: Path) -> Survey:
    root = Path(root)
    is_git = ver_git.is_repo(root)
    s = Survey(git=is_git)
    if not is_git:
        s.findings.append(warning(".", 1, "git", _NO_GIT))

    tags, s.tag_format, s.stray_tags, version_like = _tag_scan(root) if is_git else ([], None, [], False)
    s.tags = tags
    s.non_semver = version_like and not tags

    found = ver_sources.discover(root)
    s.sources = [(src.spec, ver_sources.read_raw(root, src)) for src in found]
    s.assembly_info = ver_sources.assembly_info(root)

    cl_path = _changelog_path(root)
    if cl_path:
        s.changelog = "CHANGELOG.md"
        text, _, _ = ver_changelog.read_text(cl_path)
        secs = ver_changelog.sections(text)
        s.has_unreleased = any(sec.title == "Unreleased" for sec in secs)
        s.released = [sec.title for sec in secs if sec.version is not None]

    names = ver_git.branches(root) if is_git else []
    s.roles = _roles(root, names, tags[-1] if tags else None)
    s.support = sorted(n for n in names if any(fnmatch.fnmatchcase(n, p) for p in SUPPORT_PATTERNS))
    s.layout = _layout(s.roles)

    latest_tag = None
    if tags:
        finals = [Version.parse(_TAG_RE.match(t).group("v")) for t in tags]
        finals = [v for v in finals if v.is_final]
        latest_tag = max(finals) if finals else None
    released_finals = [Version.parse(r) for r in s.released if Version.parse(r).is_final]
    latest_section = max(released_finals) if released_finals else None

    if s.non_semver:
        s.verdict = "ambiguous"
        s.stops.append("the tags are versions but not SemVer: continue the project's scheme (not supported) "
                       "or move to SemVer from the next release")
    elif tags or s.released:
        s.verdict = "released"
        s.current = str(latest_tag or latest_section) if (latest_tag or latest_section) else None
    if s.released and not tags and is_git:
        s.stops.append("the changelog has released versions but the repository has no tags: "
                       "propose tagging from the next release on")

    _check_sources(s, latest_tag)
    if latest_tag and latest_section and latest_tag != latest_section:
        s.stops.append(f"the latest tag ({latest_tag}) and the changelog's latest section ({latest_section}) disagree")
    if s.layout is None:
        s.stops.append("a staging branch exists without an integration branch: the layout is ambiguous")
    if is_git and names and s.roles["production"] is None:
        s.stops.append("no production branch can be told apart: name it")
    return s


def _check_sources(s: Survey, latest: Optional[Version]) -> None:
    plain = [(spec, raw) for spec, raw in s.sources if spec != "tag" and not spec.endswith(("-lock.json", ".lock"))]
    by_kind = {}
    for spec, raw in plain:
        kind = ver_sources.parse_source(spec).kind
        by_kind.setdefault(kind, set()).add(raw)
    if any(len(values) > 1 for kind, values in by_kind.items() if kind in ("npm", "cargo", "pyproject", "msbuild")):
        s.verdict = "ambiguous"
        s.stops.append("several unrelated versions were found (a monorepo): independently versioned packages "
                       "are not supported")
        return
    declared = {parse_declared(spec, raw) for spec, raw in plain}
    declared.discard(None)
    if len(declared) > 1:
        s.stops.append("the version sources disagree: " + ", ".join(f"{spec}={raw}" for spec, raw in plain))
        return
    if latest and declared:
        v = declared.pop()
        ok = v == latest or (not v.is_final and v.final > latest)
        if not ok:
            s.stops.append(f"the declared version ({v}) and the latest tag ({latest}) disagree")


def _pattern_prefix(pattern: str) -> str:
    return pattern.split("{", 1)[0]


def _role(branch: Optional[str], settings: Settings) -> Optional[str]:
    if branch is None:
        return None
    if branch == settings.production:
        return "production"
    if branch == settings.staging and settings.layout == "dev-staging-main":
        return "staging"
    if branch == settings.integration and settings.layout in ("dev-staging-main", "dev-main"):
        return "integration"
    if support_line(branch, settings) is not None:
        return "support"
    for role, pattern in (("release", settings.release_branch), ("hotfix", settings.hotfix_branch)):
        prefix = _pattern_prefix(pattern)
        if prefix and branch.startswith(prefix):
            return role
    return "work"


def support_line(branch: str, settings: Settings) -> Optional[tuple]:
    pattern = re.escape(settings.support_branch)
    pattern = pattern.replace(r"\{major\}", r"(?P<major>\d+)").replace(r"\{minor\}", r"(?P<minor>\d+)")
    m = re.match("^" + pattern + "$", branch)
    return (int(m.group("major")), int(m.group("minor"))) if m else None


def latest_final(root: Path, settings: Settings, line: Optional[tuple] = None) -> Optional[Version]:
    finals = [v for _, v in ver_git.tag_versions(root, settings.tag) if v.is_final]
    if line:
        finals = [v for v in finals if (v.major, v.minor) == line]
    return max(finals) if finals else None


def due(entries: dict) -> Optional[str]:
    present = [name for name, items in entries.items() if items]
    if "Security" in present:
        return "patch: Security"
    feature = [n for n in ver_changelog.ORDER[:4] if n in present]
    if feature:
        return f"minor when the milestone is finished: {feature[0]}"
    if "Fixed" in present:
        return "patch: Fixed"
    return None


def status(root: Path, settings: Settings) -> Status:
    root = Path(root)
    findings = []
    is_git = ver_git.is_repo(root)
    if not is_git:
        findings.append(warning(".", 1, "git", _NO_GIT))
    branch = ver_git.current_branch(root) if is_git else None
    role = _role(branch, settings)
    line = support_line(branch, settings) if role == "support" else None
    latest = latest_final(root, settings, line) if is_git else None

    specs = settings.sources or [src.spec for src in ver_sources.discover(root)]
    declared, versions = {}, set()
    for spec in specs:
        if spec == "tag":
            continue
        try:
            raw = ver_sources.read_raw(root, ver_sources.parse_source(spec))
        except ValueError as exc:
            findings.append(error(spec, 1, "sources", str(exc)))
            continue
        if raw is None:
            findings.append(error(spec, 1, "sources", "no version found"))
            continue
        declared[spec] = raw
        versions.add(parse_declared(spec, raw))

    cl_latest, entries = None, {}
    cl_path = _changelog_path(root, settings.changelog)
    if cl_path:
        text, _, _ = ver_changelog.read_text(cl_path)
        secs = [sec for sec in ver_changelog.sections(text) if sec.version is not None]
        cl_latest = str(max(sec.version for sec in secs)) if secs else None
        entries = ver_changelog.unreleased(text)
    return Status(settings.layout, branch, role, latest, declared, cl_latest,
                  len(versions) <= 1 and None not in versions, due(entries), findings)
