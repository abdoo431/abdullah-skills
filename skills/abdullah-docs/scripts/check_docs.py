"""Read-only done check for documentation: scope, ADR checks and the agent section.

Prints one finding per line as `path:line: severity: kind: message`, sorted by path and line.
Exit codes: 0 no errors, 1 at least one error, 2 usage error.
"""
import argparse
import fnmatch
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

import docs_adr  # noqa: E402
import docs_findings  # noqa: E402
import docs_git  # noqa: E402
import docs_markdown  # noqa: E402
import docs_policy  # noqa: E402

_LINK_RE = re.compile(r"\[[^\]]*\]\(\s*<?([^)>\s]+)")
_SCHEME_RE = re.compile(r"^[a-z][a-z0-9+.-]*:", re.I)


@dataclass
class Context:
    root: Path
    settings: docs_policy.Settings
    base: Optional[str]
    scope: Optional[set]  # None means all files
    release: bool


def _read(path: Path) -> str:
    return path.read_bytes().decode("utf-8", errors="replace")


def _adr_rel(ctx: Context) -> str:
    return ctx.settings.adr_dir.replace("\\", "/").strip("/") or "."


def _join(folder: str, name: str) -> str:
    return name if folder == "." else f"{folder}/{name}"


def _local_names(ctx: Context) -> list:
    folder = ctx.root / _adr_rel(ctx)
    return sorted(p.name for p in folder.iterdir() if p.is_file()) if folder.is_dir() else []


def is_history(ctx: Context, path: str) -> bool:
    path = path.replace("\\", "/")
    if any(fnmatch.fnmatch(path, g) for g in ctx.settings.history):
        return True
    folder, _, name = path.rpartition("/")
    if (folder or ".") == _adr_rel(ctx) and docs_adr.ADR_NAME_RE.match(name):
        try:
            status = docs_adr.status_of(_read(ctx.root / path))
        except OSError:
            return False
        return bool(status and status[1].lower().startswith("superseded"))
    return False


def severity_for(ctx: Context, path: str) -> str:
    """Severity of a content finding (link, anchor, code-path): history only warns."""
    return "warning" if is_history(ctx, path) else "error"


def build_context(args) -> tuple:
    root = Path(args.root).resolve()
    if args.policy:
        policy = Path(args.policy)
        if not policy.is_absolute() and (root / policy).exists():
            policy = root / policy
    else:
        policy = docs_policy.find_policy(root)
    settings = docs_policy.read_settings(policy)  # raises FileNotFoundError; main exits 2
    if args.adr_dir:
        settings.adr_dir = args.adr_dir
    if args.changelog:
        settings.changelog = args.changelog
    if args.pairs:
        settings.pairs = [tuple(p.partition(":")[::2]) for p in args.pairs]
    if args.history:
        settings.history = list(args.history)

    findings = []
    base = args.base or settings.base or docs_git.default_base(root)
    if not docs_git.is_repo(root):
        findings.append(docs_findings.warning(".", 1, "base", "not a git repository; checking all files"))
        base = None
    elif not base:
        findings.append(docs_findings.warning(".", 1, "base", "no base branch found; checking all files"))
    elif not docs_git.ref_exists(root, base):
        findings.append(docs_findings.warning(
            ".", 1, "base", f"base '{base}' does not exist here (fetch it?); checking all files"))
        base = None
    scope = docs_git.changed_files(root, base) if base and not args.all else None
    return Context(root, settings, base, scope, args.release), findings


def _by_number(files) -> dict:
    grouped: dict = {}
    for f in files:
        grouped.setdefault(f.number, []).append(f.name)
    return grouped


def check_adr(ctx: Context) -> list:
    folder = _adr_rel(ctx)
    names = _local_names(ctx)
    adrs = docs_adr.adr_files(names)
    out = []
    for name in docs_adr.unrecognised_adrs(names):
        out.append(docs_findings.warning(
            _join(folder, name), 1, "adr-name", "looks like an ADR but its name cannot be numbered; use NNNN-slug.md"))

    index_rel = _join(folder, "README.md")
    index_path = ctx.root / index_rel
    if adrs and not index_path.is_file():
        out.append(docs_findings.error(index_rel, 1, "adr-index", "no ADR index; add a README.md linking every ADR"))
    elif index_path.is_file():
        known = set(names)
        targets = docs_adr.index_targets(_read(index_path))
        linked = {name for _, name in targets}
        for line, name in targets:
            if name not in known:
                out.append(docs_findings.error(
                    index_rel, line, "adr-index", f"index links {name}, which does not exist"))
        for a in adrs:
            if a.name not in linked:
                out.append(docs_findings.error(
                    _join(folder, a.name), 1, "adr-index", f"{a.name} is not linked from {index_rel}"))

    on_base: dict = {}
    if ctx.base:
        on_base = _by_number(docs_adr.adr_files(docs_git.files_at(ctx.root, ctx.base, folder)))
    for number, group in sorted(_by_number(adrs).items()):
        for name in group:
            path = _join(folder, name)
            if len(group) > 1:
                out.append(docs_findings.error(
                    path, 1, "adr-number", f"number {number} is used by {' and '.join(group)}; renumber the local one"))
            taken = on_base.get(number, [])
            if len(group) == 1 and taken and name not in taken:
                out.append(docs_findings.error(
                    path, 1, "adr-number",
                    f"number {number} is used by {taken[0]} on {ctx.base}, not {name}; renumber the local one"))

    for a in adrs:
        path = _join(folder, a.name)
        text = _read(ctx.root / path)
        status = docs_adr.status_of(text)
        if not status:
            out.append(docs_findings.error(path, 1, "adr-header", "no status line"))
        elif status[1].lower().startswith("superseded"):
            for target in _LINK_RE.findall(status[1]):
                rel = target.split("#", 1)[0]
                if rel and not _SCHEME_RE.match(rel) and not (ctx.root / folder / rel).resolve().is_file():
                    out.append(docs_findings.error(
                        path, status[0], "adr-header", f"'Superseded by' link names a missing ADR: {target}"))
        if not docs_adr.date_of(text):
            out.append(docs_findings.error(path, 1, "adr-header", "no date line"))
    return out


def _has_heading(text: str) -> bool:
    fence = None
    for line in text.splitlines():
        m = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if m:
            if fence is None:
                fence = m.group(1)[0]
            elif m.group(1)[0] == fence:
                fence = None
        elif fence is None and line.rstrip() == docs_policy.AGENT_SECTION_HEADING:
            return True
    return False


def check_agent_section(ctx: Context) -> list:
    existing = [n for n in ("CLAUDE.md", "AGENTS.md") if (ctx.root / n).is_file()]
    if any(_has_heading(_read(ctx.root / n)) for n in existing):
        return []
    return [docs_findings.warning(
        existing[0] if existing else "AGENTS.md", 1, "agent-section",
        f"no '{docs_policy.AGENT_SECTION_HEADING}' section in CLAUDE.md or AGENTS.md")]


_UNRELEASED_RE = re.compile(r"^## (\[unreleased\]|unreleased)\s*$", re.I)


def _changelog_rel(ctx: Context) -> str:
    return ctx.settings.changelog.replace("\\", "/").removeprefix("./")


def _unreleased_range(lines: list):
    """(first, last) 1-based line numbers of the unreleased section, or None."""
    for i, line in enumerate(lines):
        if _UNRELEASED_RE.match(line):
            end = len(lines)
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("## "):
                    end = j
                    break
            return i + 1, end
    return None


def _history_span(ctx: Context, path: str, text: str):
    """The unreleased span when path is the changelog (lines outside it are history), else None."""
    if path != _changelog_rel(ctx):
        return None
    return _unreleased_range(docs_markdown.split_lines(text))


def _outside(span, line: int) -> bool:
    return span is not None and not span[0] <= line <= span[1]


def _markdown_files(ctx: Context) -> list:
    if ctx.scope is None:
        return [p for p in docs_git.tracked_files(ctx.root, "*.md") if (ctx.root / p).is_file()]
    return sorted(p for p in ctx.scope if p.endswith(".md") and (ctx.root / p).is_file())


def _exists_from(ctx: Context, path: str, target: str) -> bool:
    folder = (ctx.root / path).parent
    return (folder / target).exists()


def check_links(ctx: Context) -> list:
    out = []
    cache: dict = {}

    def slugs(file: Path) -> set:
        if file not in cache:
            cache[file] = docs_markdown.heading_slugs(_read(file))
        return cache[file]

    for path in _markdown_files(ctx):
        text = _read(ctx.root / path)
        span = _history_span(ctx, path, text)

        def sev(line: int) -> str:
            return "warning" if _outside(span, line) else severity_for(ctx, path)

        for link in docs_markdown.links(text):
            if link.target.startswith("/"):
                continue
            file = ctx.root / path if not link.target else (ctx.root / path).parent / link.target
            if link.target and not file.exists():
                out.append(docs_findings.Finding(
                    path, link.line, sev(link.line), "link", f"link target does not exist: {link.target}"))
            elif link.anchor and file.is_file() and file.suffix.lower() == ".md" \
                    and link.anchor.lower() not in slugs(file):
                out.append(docs_findings.warning(
                    path, link.line, "anchor",
                    f"no heading matches anchor #{link.anchor} in {link.target or path}"))
    return out


def check_code_paths(ctx: Context) -> list:
    out = []
    for path in _markdown_files(ctx):
        if any(fnmatch.fnmatch(path, g) for g in ctx.settings.examples):
            continue
        text = _read(ctx.root / path)
        span = _history_span(ctx, path, text)
        for line, token in docs_markdown.code_paths(text):
            if (ctx.root / token).exists() or _exists_from(ctx, path, token):
                continue
            severity = "warning" if _outside(span, line) else severity_for(ctx, path)
            out.append(docs_findings.Finding(path, line, severity, "code-path", f"path does not exist: {token}"))
    return out


def check_changelog(ctx: Context) -> list:
    rel = _changelog_rel(ctx)
    if not rel or not (ctx.root / rel).is_file():
        return []
    lines = docs_markdown.split_lines(_read(ctx.root / rel))
    span = _unreleased_range(lines)
    if span is None:
        return [docs_findings.error(rel, 1, "changelog", "no '## [Unreleased]' section")]
    if not ctx.base or ctx.release:
        return []
    point = docs_git.merge_base(ctx.root, ctx.base)
    if not point or docs_git.git(ctx.root, "cat-file", "-e", f"{point}:{rel}") is None:
        return []  # no changelog at the merge base: new or imported, nothing to misplace
    out = []
    for n in sorted(docs_git.added_lines(ctx.root, ctx.base, rel)):
        if n <= len(lines) and n > span[1] and lines[n - 1].strip():
            out.append(docs_findings.error(
                rel, n, "changelog",
                "line added below the Unreleased section; move it under Unreleased"))
    return out


def _glob_regex(glob: str):
    parts = re.split(r"\*+", glob)
    return re.compile("^" + "(.*)".join(re.escape(p) for p in parts) + "$")


def _counterpart(path: str, src: str, dst: str):
    m = _glob_regex(src).match(path)
    if not m:
        return None
    pieces = dst.split("*")
    groups = list(m.groups())
    if len(pieces) - 1 > len(groups):
        return None
    return "".join(p + (groups[i] if i < len(groups) and i < len(pieces) - 1 else "")
                   for i, p in enumerate(pieces))


def check_pairs(ctx: Context) -> list:
    if not ctx.settings.pairs:
        return []
    files = docs_git.tracked_files(ctx.root, "*") if ctx.scope is None else ctx.scope
    files = sorted(p for p in files if (ctx.root / p).is_file())
    changed = docs_git.changed_files(ctx.root, ctx.base) if ctx.base else None
    out = []
    for a, b in ctx.settings.pairs:
        for path in files:
            if fnmatch.fnmatch(path, b):
                other = _counterpart(path, b, a)
            elif fnmatch.fnmatch(path, a):
                other = _counterpart(path, a, b)
            else:
                continue
            if other is None:
                continue
            if not (ctx.root / other).is_file():
                out.append(docs_findings.error(path, 1, "pair", f"no counterpart {other}"))
            elif changed is not None and path in changed and other not in changed:
                out.append(docs_findings.error(
                    path, 1, "pair", f"changed since {ctx.base} but its counterpart {other} did not"))
    return out


CHECKS: list = [check_adr, check_agent_section, check_links, check_code_paths, check_changelog, check_pairs]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    ap.add_argument("--base")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--release", action="store_true")
    ap.add_argument("--adr-dir")
    ap.add_argument("--changelog")
    ap.add_argument("--pairs", action="append")
    ap.add_argument("--history", action="append")
    ap.add_argument("--policy")
    args = ap.parse_args(argv)
    if not Path(args.root).is_dir():
        print(f"check_docs.py: error: --root is not a directory: {args.root}", file=sys.stderr)
        return 2
    try:
        ctx, findings = build_context(args)
    except OSError:
        print(f"check_docs.py: error: policy file not found: {args.policy}", file=sys.stderr)
        return 2
    for check in CHECKS:
        findings.extend(check(ctx))
    for f in sorted(findings, key=lambda f: (f.path, f.line, f.kind)):
        print(docs_findings.format_finding(f))
    return docs_findings.exit_code(findings)


if __name__ == "__main__":
    sys.exit(main())
