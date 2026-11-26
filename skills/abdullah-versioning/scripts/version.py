"""Own a project's version: survey it, report its status, propose and cut releases.

Commands (each takes --root, default the current folder, and --policy, default the first
of docs/RELEASING.md, RELEASING.md, CONTRIBUTING.md, docs/DOCUMENTATION.md holding an
abdullah-versioning block):

  survey [--json]                     what the setup needs: tags, sources, changelog, branches, verdict
  status [--json]                     layout, branch role, latest release, declared versions, release due
  plan [--pre STAGE] [--major] [--json]
                                      the proposed next version and the entries that decide it
  notes X.Y.Z                         print a released section of the changelog
  check                               declared versions, branch role and changelog order agree
  prepare X.Y.Z [--pre STAGE] [--date YYYY-MM-DD] [--first-major] [--allow-long-lived]
                                      the cut: move [Unreleased] into [X.Y.Z], declare X.Y.Z or its first pre-release
  declare VERSION [--date YYYY-MM-DD] [--first-major] [--allow-long-lived]
                                      write a version into every source (next rc.N, final, -dev, or a branch's own)
  carry X.Y.Z --from REF              copy a released section from another branch's changelog

The script never fetches, commits, tags, pushes or calls a hosting service.
Findings print one per line as path:line: severity: kind: message.
Exit codes: 0 done or clean, 1 refused or errors found (nothing written), 2 usage error.
"""
import argparse
import json
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ver_changelog  # noqa: E402
import ver_findings  # noqa: E402
import ver_git  # noqa: E402
import ver_plan  # noqa: E402
import ver_policy  # noqa: E402
import ver_semver  # noqa: E402
import ver_sources  # noqa: E402
import ver_survey  # noqa: E402
from ver_semver import STAGES, Version  # noqa: E402

COMMANDS = ("survey", "status", "plan", "notes", "check", "prepare", "declare", "carry")


class Refused(Exception):
    """A command refused before writing anything."""


def _version_arg(text: str) -> Version:
    try:
        return Version.parse(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from None


def _parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="version.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True, metavar="command")

    def command(name: str, help_text: str) -> argparse.ArgumentParser:
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--root", default=".", help="the repository root (default: current folder)")
        p.add_argument("--policy", help="the release policy file holding the abdullah-versioning block")
        return p

    p = command("survey", "survey the project for the setup")
    p.add_argument("--json", action="store_true")
    p = command("status", "report the release status")
    p.add_argument("--json", action="store_true")
    p = command("plan", "propose the next version")
    p.add_argument("--pre", choices=STAGES)
    p.add_argument("--major", action="store_true", help="a Changed entry breaks existing use")
    p.add_argument("--json", action="store_true")
    p = command("notes", "print a released changelog section")
    p.add_argument("version", type=_version_arg)
    command("check", "check declared versions, branch role and changelog")
    for name, help_text in (("prepare", "cut a release"), ("declare", "write a version into every source")):
        p = command(name, help_text)
        p.add_argument("version", type=_version_arg)
        if name == "prepare":
            p.add_argument("--pre", help="pre-release stage: alpha, beta or rc")
        p.add_argument("--date", help="the release date, YYYY-MM-DD (default: today)")
        p.add_argument("--first-major", action="store_true", help="the owner declared 1.0.0 or later")
        p.add_argument("--allow-long-lived", action="store_true",
                       help="allow the change on the production, staging or integration branch itself")
    p = command("carry", "copy a released changelog section from another branch")
    p.add_argument("version", type=_version_arg)
    p.add_argument("--from", dest="ref", required=True, help="the branch or tag to copy from")
    return ap


def _settings(args) -> ver_policy.Settings:
    root = Path(args.root)
    policy = Path(args.policy) if args.policy else ver_policy.find_policy(root)
    return ver_policy.read_settings(policy)


def _print_findings(findings: list) -> None:
    for f in findings:
        print(ver_findings.format_finding(f))


def _survey(args) -> int:
    s = ver_survey.survey(Path(args.root))
    if args.json:
        print(s.to_json())
        return 0
    print(f"verdict: {s.verdict}")
    print(f"current: {s.current or 'none'}")
    print(f"layout: {s.layout or 'unknown'}")
    for role, name in s.roles.items():
        print(f"{role}: {name or 'none'}")
    print(f"tags: {', '.join(s.tags) or 'none'}")
    print(f"tag-format: {s.tag_format or 'none'}")
    for spec, raw in s.sources:
        print(f"source: {spec} = {raw or 'tag'}")
    print(f"changelog: {s.changelog or 'none'}")
    for stop in s.stops:
        print(f"stop: {stop}")
    _print_findings(s.findings)
    return 0


def _status(args) -> int:
    st = ver_survey.status(Path(args.root), _settings(args))
    if args.json:
        data = asdict(st)
        data["latest"] = str(st.latest) if st.latest else None
        data["findings"] = [ver_findings.format_finding(f) for f in st.findings]
        print(json.dumps(data, indent=2))
        return 0
    print(f"layout: {st.layout or 'unknown'}")
    print(f"branch: {st.branch or 'none'}")
    print(f"role: {st.role or 'none'}")
    print(f"latest: {st.latest or 'none'}")
    for spec, raw in st.declared.items():
        print(f"declared: {spec} = {raw}")
    print(f"agree: {'yes' if st.agree else 'no'}")
    print(f"changelog: {st.changelog_latest or 'none'}")
    print(f"due: {st.due or 'none'}")
    _print_findings(st.findings)
    return 0


def _changelog_text(root: Path, settings) -> str:
    path = root / settings.changelog
    if not path.is_file():
        raise Refused(f"{settings.changelog} does not exist")
    return ver_changelog.read_text(path)[0]


def _plan(args) -> int:
    root, settings = Path(args.root), _settings(args)
    st = ver_survey.status(root, settings)
    entries = ver_changelog.unreleased(_changelog_text(root, settings))
    existing = [v for _, v in ver_git.tag_versions(root, settings.tag) if not v.is_final]
    p = ver_plan.propose(st.latest, entries, first=Version.parse(settings.first_version), pre=args.pre,
                         major=args.major, existing=existing)
    if args.json:
        print(json.dumps({"current": str(p.current) if p.current else None, "next": str(p.next), "part": p.part,
                          "reasons": p.reasons, "judgment": p.judgment, "pre": p.pre}, indent=2))
        return 0
    print(f"current: {p.current or 'none'}")
    print(f"next: {p.next}")
    print(f"part: {p.part}")
    for reason in p.reasons:
        print(f"reason: {reason}")
    for item in p.judgment:
        print(f"judge: {item}")
    return 0


def _notes(args) -> int:
    root, settings = Path(args.root), _settings(args)
    try:
        print(ver_changelog.section_body(_changelog_text(root, settings), args.version))
    except ValueError as exc:
        raise Refused(str(exc)) from None
    return 0


def _role_finding(st, settings, declared: Version):
    latest, role = st.latest, st.role
    path = next(iter(st.declared), ".")
    if role == "integration":
        if settings.dev_suffix:
            ok = declared.stage == settings.dev_suffix and (latest is None or declared.final > latest)
            want = f"a -{settings.dev_suffix} version above {latest or 'the last release'}"
        else:
            ok = latest is None or declared == latest
            want = f"{latest}"
    elif role == "staging":
        ok = latest is None or (declared.final > latest if not declared.is_final else declared >= latest)
        want = f"a pre-release or release above {latest}"
    elif role == "production":
        if latest is not None and declared.is_final and declared > latest:
            return ver_findings.warning(path, 1, "role", f"{declared} is declared but not tagged yet (untagged release)")
        ok = latest is None or declared == latest
        want = f"{latest}"
    elif role == "support":
        line = ver_survey.support_line(st.branch, settings)
        ok = line is not None and (declared.major, declared.minor) == line and (latest is None or declared >= latest)
        want = f"a version in the {line[0]}.{line[1]} line" if line else "a version in the branch's line"
    else:
        return None
    if ok:
        return None
    return ver_findings.error(path, 1, "role", f"the {role} branch declares {declared}; it should declare {want}")


def _check(args) -> int:
    root, settings = Path(args.root), _settings(args)
    st = ver_survey.status(root, settings)
    findings = list(st.findings)
    parsed = {spec: ver_survey.parse_declared(spec, raw) for spec, raw in st.declared.items()}
    if not st.agree:
        detail = ", ".join(f"{spec}={raw}" for spec, raw in st.declared.items())
        findings.append(ver_findings.error(next(iter(st.declared), "."), 1, "sources", f"the declared versions disagree: {detail}"))
    elif parsed:
        f = _role_finding(st, settings, next(iter(parsed.values())))
        if f:
            findings.append(f)
    cl_path = root / settings.changelog
    if cl_path.is_file():
        for line, message in ver_changelog.problems(ver_changelog.read_text(cl_path)[0]):
            findings.append(ver_findings.error(settings.changelog, line, "changelog", message))
    _print_findings(findings)
    return ver_findings.exit_code(findings)


# --- the writing commands ------------------------------------------------------------

class _Context:
    """What every writing command needs, read once before anything is written."""

    def __init__(self, args):
        self.root = Path(args.root)
        self.settings = _settings(args)
        self.status = ver_survey.status(self.root, self.settings)
        specs = self.settings.sources or [s.spec for s in ver_sources.discover(self.root)]
        if not specs:
            raise Refused("no version sources: run the setup first")
        self.sources = [ver_sources.parse_source(spec) for spec in specs]
        errors = [f for f in self.status.findings if f.severity == "error"]
        if errors:
            raise Refused(errors[0].message)
        if not self.status.agree:
            detail = ", ".join(f"{spec}={raw}" for spec, raw in self.status.declared.items())
            raise Refused(f"the declared versions already disagree: {detail}")
        tags = ver_git.tag_versions(self.root, self.settings.tag)
        self.finals = [v for _, v in tags if v.is_final]
        self.pres = [v for _, v in tags if not v.is_final]
        self.branches = ver_git.branches(self.root)
        self.declared = next((ver_survey.parse_declared(s, r) for s, r in self.status.declared.items()), None)

    def latest_for(self, target: Version):
        """The latest final release the target must exceed (C19, C21)."""
        if not self.finals:
            return None
        line = (target.major, target.minor)
        newest = max(self.finals)
        support = self.settings.support_branch.replace("{major}", str(line[0])).replace("{minor}", str(line[1]))
        if self.status.role == "support" or (target.final < newest and support in self.branches):
            in_line = [v for v in self.finals if (v.major, v.minor) == line]
            return max(in_line) if in_line else None
        return newest

    def tag_of(self, v: Version) -> str:
        return self.settings.tag.replace("{version}", str(v))


def _check_target(ctx: _Context, target: Version, args, *, strict: bool) -> None:
    role = ctx.status.role
    if role in ("production", "staging", "integration") and not args.allow_long_lived:
        raise Refused(f"{ctx.status.branch} is the {role} branch: change the version on a release or hotfix "
                      "branch, or pass --allow-long-lived for a local merge")
    if role == "support":
        line = ver_survey.support_line(ctx.status.branch, ctx.settings)
        if line and (target.major, target.minor) != line:
            raise Refused(f"{target} is outside the {line[0]}.{line[1]} line of {ctx.status.branch}")
    if target.final.major >= 1 and not any(v.major >= 1 for v in ctx.finals) and not args.first_major:
        raise Refused(f"{target} would be the first 1.0.0 or later: only the owner declares it (--first-major)")
    if ctx.declared is not None and target == ctx.declared and not strict:
        return
    latest = ctx.latest_for(target)
    if latest is not None and not (target.final > latest):
        raise Refused(f"{target} is not after the latest release, {latest}")
    if not target.is_final and target.stage in STAGES:
        same = [v for v in ctx.pres if v.final == target.final and v.stage in STAGES]
        if same:
            top = max(same)
            if STAGES.index(target.stage) < STAGES.index(top.stage):
                raise Refused(f"{top} exists: a pre-release never goes back to {target.stage}")
            if target < top:
                raise Refused(f"{target} is below {top}, which already exists")


def _write_all(ctx: _Context, changelog_text, target: Version) -> list:
    written = []
    for src in ctx.sources:
        if src.kind != "tag" and ver_sources.read_raw(ctx.root, src) is None:
            raise Refused(f"{src.path}: no version found")
    if changelog_text is not None:
        path = ctx.root / ctx.settings.changelog
        _, newline, bom = ver_changelog.read_text(path)
        ver_changelog.write_text(path, changelog_text, newline, bom)
        written.append(ctx.settings.changelog)
    for src in ctx.sources:
        if src.kind == "tag":
            continue
        ver_sources.write_version(ctx.root, src, target)
        written.append(src.path)
    return written


def _today(args) -> str:
    return args.date or date.today().isoformat()


def _prepare(args) -> int:
    ctx = _Context(args)
    final = args.version
    if not final.is_final:
        raise Refused("prepare takes a release version X.Y.Z; use --pre for a pre-release")
    if args.pre and args.pre not in STAGES:
        raise Refused(f"{args.pre!r} is not a pre-release stage: use alpha, beta or rc")
    target = ver_semver.next_pre(final, args.pre, ctx.pres) if args.pre else final
    _check_target(ctx, target, args, strict=True)
    text = _changelog_text(ctx.root, ctx.settings)
    latest = ctx.latest_for(final)
    new_text = ver_changelog.cut(text, final, _today(args), ctx.tag_of(latest) if latest else None, ctx.settings.tag)
    for path in _write_all(ctx, new_text, target):
        print(f"wrote: {path}")
    print(f"declared: {target}")
    for bullet in ver_changelog.fold_candidates(new_text, final):
        print(f"fold: {bullet.splitlines()[0]}")
    return 0


def _declare(args) -> int:
    ctx = _Context(args)
    target = args.version
    _check_target(ctx, target, args, strict=False)
    new_text = None
    if target.is_final or target.stage in STAGES:
        text = _changelog_text(ctx.root, ctx.settings) if (ctx.root / ctx.settings.changelog).is_file() else None
        is_open = text is not None and target.final not in ctx.finals and any(
            s.version == target.final for s in ver_changelog.sections(text))
        if is_open:
            new_text = ver_changelog.fold_unreleased_into(text, target.final)
            if target.is_final:
                new_text = ver_changelog.set_date(new_text, target.final, _today(args))
            if new_text == text:
                new_text = None
    for path in _write_all(ctx, new_text, target):
        print(f"wrote: {path}")
    print(f"declared: {target}")
    return 0


def _carry(args) -> int:
    root, settings = Path(args.root), _settings(args)
    other = ver_git.show(root, args.ref, settings.changelog)
    if other is None:
        raise Refused(f"{args.ref} has no {settings.changelog}")
    other = other.replace("\r\n", "\n")
    sec = next((s for s in ver_changelog.sections(other) if s.version == args.version), None)
    if sec is None:
        raise Refused(f"{args.ref} has no [{args.version}] section")
    lines = other.split("\n")
    block = "\n".join([lines[sec.start], "", ver_changelog.section_body(other, args.version)])
    path = root / settings.changelog
    text, newline, bom = ver_changelog.read_text(path)
    ver_changelog.write_text(path, ver_changelog.insert_section(text, block, args.version), newline, bom)
    print(f"wrote: {settings.changelog}")
    return 0


HANDLERS = {"survey": _survey, "status": _status, "plan": _plan, "notes": _notes, "check": _check,
            "prepare": _prepare, "declare": _declare, "carry": _carry}


def main(argv=None) -> int:
    ver_findings.use_utf8_output()
    try:
        args = _parser().parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0)
    try:
        return HANDLERS[args.command](args)
    except (Refused, ValueError) as exc:
        print(f"version.py: refused: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
