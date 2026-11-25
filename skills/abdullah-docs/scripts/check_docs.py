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
                out.append(docs_findings.error(index_rel, line, "adr-index", f"index links {name}, which does not exist"))
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


CHECKS: list = [check_adr, check_agent_section]


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
