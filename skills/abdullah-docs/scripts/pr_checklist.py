"""Print what the branch's diff shows for each definition-of-done item.

Read-only and decides nothing: the agent fills the PR template from these lines.
Exit codes: 0 done (a `warning: base` line comes first when there is no base), 2 usage error.
"""
import argparse
import fnmatch
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import docs_findings  # noqa: E402
import docs_git  # noqa: E402
import docs_policy  # noqa: E402

_TEST_NAMES = ("*_test.*", "*.test.*", "test_*.*")
_REFS = re.compile(r"^Refs:", re.M)


def _fail(message: str) -> int:
    print(f"pr_checklist.py: error: {message}", file=sys.stderr)
    return 2


def _is_test(path: str) -> bool:
    parts = path.split("/")
    if any(p in ("test", "tests") for p in parts[:-1]):
        return True
    return any(fnmatch.fnmatchcase(parts[-1], pat) for pat in _TEST_NAMES)


def _is_source(path: str) -> bool:
    return not path.lower().endswith(".md") and not path.startswith("docs/") and not _is_test(path)


def _under(files, folder: str) -> list[str]:
    prefix = folder.replace("\\", "/").strip("/") + "/"
    return [f for f in files if f.startswith(prefix)]


def _join(items) -> str:
    return ", ".join(sorted(items))


def _new_files(root: Path, point: str | None) -> set[str]:
    new = set(docs_git._untracked(root))
    if point:
        out = docs_git.git(root, "diff", "--no-color", "--no-ext-diff", "--name-only",
                           "--diff-filter=A", "--relative", point)
        new.update(docs_git._lines(out))
    return new


def main(argv=None) -> int:
    docs_findings.use_utf8_output()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    ap.add_argument("--base")
    ap.add_argument("--policy")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        return _fail(f"--root is not a directory: {args.root}")
    if args.policy:
        policy = Path(args.policy)
        if not policy.is_absolute() and (root / policy).exists():
            policy = root / policy
    else:
        policy = docs_policy.find_policy(root)
    try:
        settings = docs_policy.read_settings(policy)
    except (FileNotFoundError, OSError):
        return _fail(f"policy file not found: {args.policy}")

    base = args.base or settings.base or docs_git.default_base(root)
    out = []
    usable = False
    if not base:
        msg = "no base branch found; showing uncommitted and untracked files only"
    elif not docs_git.is_repo(root):
        msg = "not a git repository; showing no changes"
    elif not docs_git.ref_exists(root, base):
        msg = f"base '{base}' does not exist here (fetch it?); showing uncommitted and untracked files only"
    elif not docs_git.merge_base(root, base):
        msg = f"no merge base with '{base}'; showing uncommitted and untracked files only"
    else:
        usable = True
    if not usable:
        out.append(docs_findings.format_finding(docs_findings.warning(".", 1, "base", msg)))
        base = None

    changed = {f for f in docs_git.changed_files(root, base) if (root / f).is_file()}
    point = docs_git.merge_base(root, base) if base else None
    if point is None and docs_git.is_repo(root) and docs_git.ref_exists(root, "HEAD"):
        point = "HEAD"
    new = {f for f in _new_files(root, point) if (root / f).is_file()}
    commits = docs_git.commits_since(root, base) if base else []

    spec = [f for f in changed
            if any(_under([f], d) for d in (settings.adr_dir, settings.specs, settings.plans))]
    changelog = settings.changelog.replace("\\", "/").removeprefix("./")  # as check_docs.py reads it
    sources = [f for f in changed if _is_source(f)]
    new_sources = [f for f in new if _is_source(f)]
    tests = [f for f in changed if _is_test(f)]
    runbooks = _under(new, "docs/runbooks")

    interface = "check by hand"
    if new_sources:
        interface += f" (new source files: {_join(new_sources)})"
    if not any(_REFS.search(c) for c in commits):
        refs = "n/a (no commit uses Refs:)"
    else:
        missing = [c.splitlines()[0] for c in commits if not _REFS.search(c)]
        refs = "; ".join(missing) if missing else "all commits reference"

    out += [
        f"- spec-or-adr: {_join(spec) if spec else 'none changed'}",
        f"- changelog: {'changed' if changelog in changed else 'not changed'} ({len(sources)} source files changed)",
        f"- public-interface: {interface}",
        f"- regression-test: {_join(tests) if tests else 'none changed'}",
        f"- runbook: {_join(runbooks) if runbooks else 'none added'}",
        f"- commit-refs: {refs}",
    ]
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
